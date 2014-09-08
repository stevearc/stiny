package main

import (
	"os"
	"os/exec"

	"github.com/stevearc/pike"
	"github.com/stevearc/pike/plog"
)

func javascript(debug bool) []*pike.Graph {
	graphs := make([]*pike.Graph, 0, 3)

	p := pike.Glob("stiny/static", "lib/angular.*", "lib/*.js")
	libjs := p
	if debug {
		p = p.Pipe(pike.ChangeFilter())
		p = p.Pipe(pike.Write("stiny/gen"))
		p = p.Pipe(pike.Json("lib.js"))
		g := pike.NewGraph("lib.js")
		g.Add(p)
		graphs = append(graphs, g)
	}

	p = pike.Glob("stiny/static", "app/*.html")
	templates := p
	if debug {
		p = p.Pipe(pike.ChangeFilter())
		p = p.Pipe(pike.Write("stiny/gen"))
		g := pike.NewGraph("app.html")
		g.Add(p)
		graphs = append(graphs, g)
	} else {
		hash := getHash()
		templates = p.Pipe(pike.HtmlTemplateCache("stiny", "gen/"+hash))
	}

	p = pike.Glob("stiny/static", "app/app.coffee", "app/*.coffee")
	if debug {
		p = p.Pipe(pike.ChangeFilter())
		p = p.Fork(pike.Coffee(), 0, 0)
	} else {
		p = p.Fork(pike.Coffee(), 0, 1)
		m := libjs.Pipe(pike.Merge())
		p.Pipe(m)
		templates.Pipe(m)
		p = m.Pipe(pike.Concat("app.js"))
		p = p.Pipe(pike.Uglify())
	}
	p = p.Xargs(pike.Write("stiny/gen"), 0)
	p = p.Pipe(pike.Json("app.js"))
	g := pike.NewGraph("app.js")
	g.Add(p)
	graphs = append(graphs, g)

	return graphs
}

func css(debug bool) []*pike.Graph {
	graphs := make([]*pike.Graph, 0, 2)

	var p *pike.Node
	var libcss *pike.Node
	if debug {
		p = pike.Glob("stiny/static", "lib/*.css", "!lib/*.min.css")
		p = p.Pipe(pike.ChangeFilter())
		p = p.Pipe(pike.Write("stiny/gen"))
		p = p.Pipe(pike.Json("lib.css"))
		g := pike.NewGraph("lib.css")
		g.Add(p)
		graphs = append(graphs, g)
	} else {
		libcss = pike.Glob("stiny/static", "lib/*.min.css")
	}

	p = pike.Glob("stiny/static", "lib/*.otf", "lib/*.eot", "lib/*.svg", "lib/*.ttf", "lib/*.woff")
	if debug {
		p = p.Pipe(pike.ChangeFilter())
	} else {
		p = p.Pipe(pike.Rename("fonts/{{.Name}}"))
	}
	p = p.Pipe(pike.Write("stiny/gen"))
	g := pike.NewGraph("lib.fonts")
	g.Add(p)
	graphs = append(graphs, g)

	p = pike.Glob("stiny/static/app", "app.less")
	if debug {
		all := pike.Glob("stiny/static/app", "*.less")
		p = p.Pipe(pike.ChangeWatcher())
		all.Pipe(p)
		p = p.Pipe(pike.Less())
	} else {
		p = p.Pipe(pike.Less())
		merge := libcss.Pipe(pike.Merge())
		p = p.Pipe(merge)
		p = p.Pipe(pike.Concat("app.css"))
		p = p.Pipe(pike.CleanCss())
		p = p.Pipe(pike.Rename("css/{{.Name}}"))
	}
	p = p.Pipe(pike.Write("stiny/gen"))
	p = p.Pipe(pike.Json("app.less"))
	g = pike.NewGraph("app.less")
	g.Add(p)
	graphs = append(graphs, g)

	return graphs
}

func makeAllGraphs(watch bool) []*pike.Graph {
	os.RemoveAll("stiny/gen")

	allGraphs := make([]*pike.Graph, 0, 10)

	allGraphs = append(allGraphs, javascript(watch)...)
	allGraphs = append(allGraphs, css(watch)...)
	return allGraphs
}

func getHash() string {
	cmd := exec.Command("git", "rev-parse", "HEAD")
	cmd.Stderr = os.Stderr
	output, err := cmd.Output()
	if err != nil {
		plog.Exc(err)
		return ""
	}
	return string(output[:8])
}

func main() {
	pike.SetJsonFile("stiny/files.json")
	pike.SetJsonPretty(true)
	pike.Start(makeAllGraphs)
}
