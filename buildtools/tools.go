// +build tools

package tools

/*
 * list of modules required to build and run all tests
 * see: https://github.com/golang/go/wiki/Modules#how-can-i-track-tool-dependencies-for-a-module
 * and: https://github.com/go-modules-by-example/index/blob/master/010_tools/README.md
 */

import (
	_ "github.com/davecgh/go-spew/spew"
	_ "golang.org/x/tools/cmd/goimports"
	_ "github.com/sni/copyfighter"
	_ "github.com/golangci/golangci-lint/cmd/golangci-lint"
	_ "golang.org/x/tools/cmd/stringer"
)
