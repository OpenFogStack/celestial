/*
 * This file is part of Celestial (https://github.com/OpenFogStack/celestial).
 * Copyright (c) 2024 Soeren Becker, Nils Japke, Tobias Pfandzelter, The
 * OpenFogStack Team.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 **/

#include <stdint.h>
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/stddef.h>
#include <linux/in.h>
#include <linux/ip.h>
#include <linux/pkt_cls.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include "helpers.h"
#include "maps.h"

/* Adapted from: https://elixir.bootlin.com/linux/latest/source/tools/testing/selftests/bpf/progs/test_tc_edt.c
       and from:  https://github.com/srnbckr/ebpf-network-emulation/blob/main/cmd/ebpf-network-emulation/ebpf/network_simulation.c*/

/* the maximum delay we are willing to add (drop packets beyond that) */
#define TIME_HORIZON_NS (2000 * 1000 * 1000)
#define NS_PER_SEC 1000000000
#define ECN_HORIZON_NS 999999000000
#define NS_PER_US 1000

/* flow_key => last_tstamp timestamp used */
struct
{
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, uint32_t);
    __type(value, uint64_t);
    __uint(max_entries, 65535);
} flow_map SEC(".maps");

static inline int throttle_flow(struct __sk_buff *skb, __u32 ip_address, uint32_t *throttle_rate_kbps)
{

    // find out if the packet should be dropped (i.e. if the rate is 0)
    if (*throttle_rate_kbps == 0)
    {
        return TC_ACT_SHOT;
        // TODO: originally I wanted to set a mark and have iptables reject
        // packets with that mark with a nice icmp-net-unreachable error.
        // unfortunately, this does not work, because the mark is not set
        // until AFTER the packet is processed by iptables (because it is
        // further up the stack than our tc hook). In theory we could do
        // something with incoming packets (on the sender side), but that
        // would require us to built a separate ebpf program for that.
        // set the mark to 1 at bit 7 so we can have an iptables filter for it
        //        skb->mark = skb->mark | 0x80;
        //        return TC_ACT_OK;
    }

    // use ip as key in map
    uint32_t key = ip_address;

    // when was the last packet sent?
    uint64_t *last_tstamp = bpf_map_lookup_elem(&flow_map, &key);
    // calculate delay between packets based on bandwidth and packet size (kbps = byte/1000/second)
    uint64_t delay_ns = ((uint64_t)skb->len) * NS_PER_SEC / 1000 / *throttle_rate_kbps;

    uint64_t now = bpf_ktime_get_ns();
    uint64_t tstamp, next_tstamp = 0;

    // calculate the next timestamp
    if (last_tstamp)
        next_tstamp = *last_tstamp + delay_ns;

    // if the current timestamp of the packet is in the past, use the current time
    tstamp = skb->tstamp;
    if (tstamp < now)
        tstamp = now;

    // if the delayed timestamp is already in the past, send the packet
    if (next_tstamp <= tstamp)
    {
        // setting the timestamp
        // if it does not work, drop the packet
        if (bpf_map_update_elem(&flow_map, &key, &tstamp, BPF_ANY))
            return TC_ACT_SHOT;

        return TC_ACT_OK;
    }

    // do not queue for more than 2s, just drop packet instead
    if (next_tstamp - now >= TIME_HORIZON_NS)
        return TC_ACT_SHOT;

    /* set ecn bit, if needed */
    if (next_tstamp - now >= ECN_HORIZON_NS)
        bpf_skb_ecn_set_ce(skb);

    // update last timestamp in map
    if (bpf_map_update_elem(&flow_map, &key, &next_tstamp, BPF_EXIST))
        return TC_ACT_SHOT;

    // set delayed timestamp for packet
    skb->tstamp = next_tstamp;

    // OK means we can go on to set additional delay
    return TC_ACT_OK;
}

static inline int inject_delay(struct __sk_buff *skb, uint32_t *delay_us)
{
    uint64_t delay_ns = (*delay_us) * NS_PER_US;

    // sometimes skb-tstamp is reset to 0
    // https://patchwork.kernel.org/project/netdevbpf/patch/20220301053637.930759-1-kafai@fb.com/
    // check if skb->tstamp == 0
    if (skb->tstamp == 0)
    {
        skb->tstamp = bpf_ktime_get_ns() + delay_ns;
        return TC_ACT_OK;
    }

    uint64_t new_ts = ((uint64_t)skb->tstamp) + delay_ns;
    // otherwise add additional delay to packets
    skb->tstamp = new_ts;

    return TC_ACT_OK;
}

SEC("tc")
int tc_main(struct __sk_buff *skb)
{
    // data_end is a void* to the end of the packet. Needs weird casting due to kernel weirdness.
    void *data_end = (void *)(unsigned long long)skb->data_end;
    // data is a void* to the beginning of the packet. Also needs weird casting.
    void *data = (void *)(unsigned long long)skb->data;

    // nh keeps track of the beginning of the next header to parse
    struct hdr_cursor nh;

    struct ethhdr *eth;
    struct iphdr *iphdr;

    int eth_type;
    int ip_type;

    // start parsing at beginning of data
    nh.pos = data;

    // parse ethernet
    eth_type = parse_ethhdr(&nh, data_end, &eth);
    if (eth_type == bpf_htons(ETH_P_IP))
    {
        ip_type = parse_iphdr(&nh, data_end, &iphdr);
        if (ip_type == IPPROTO_ICMP || ip_type == IPPROTO_TCP || ip_type == IPPROTO_UDP)
        {
            // source IP, to be used as map lookup key
            // see above
            __u32 ip_address = iphdr->saddr;
            __u32 *throttle_rate_kbps;
            __u32 *delay_us;

            struct handle_kbps_delay *val_struct;
            // Map lookup
            val_struct = bpf_map_lookup_elem(&IP_HANDLE_KBPS_DELAY, &ip_address);

            // Safety check, go on if no handle could be retrieved
            if (!val_struct)
            {
                return TC_ACT_OK;
            }

            throttle_rate_kbps = &val_struct->throttle_rate_kbps;
            // Safety check, go on if no handle could be retrieved
            if (!throttle_rate_kbps)
            {
                return TC_ACT_OK;
            }

            int ret = throttle_flow(skb, ip_address, throttle_rate_kbps);

            if (ret != TC_ACT_OK)
            {
                return ret;
            }

            // packet OK, add delay
            delay_us = &val_struct->delay_us;

            // Safety check, go on if no handle could be retrieved
            if (!delay_us)
            {
                return TC_ACT_OK;
            }

            return inject_delay(skb, delay_us);
        }
    }
    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
