package info

type Identifier struct {
	Shell uint8
	ID    uint32
	Name  string
}

type Node struct {
	Type       string
	Active     bool
	Identifier Identifier
}

type Shell struct {
	Sats []Node
}

type Constellation struct {
	Shells         []Shell
	Groundstations []Node
}

type Segment struct {
	Source    Identifier
	Target    Identifier
	Delay     uint32
	Bandwidth uint64
}

type Path struct {
	Source    Identifier
	Target    Identifier
	Delay     uint32
	Bandwidth uint64
	Segments  []Segment
}
