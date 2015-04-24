#!/bin/bash -e

dl () {
    local name=$1
    local url=$2
    local args=
    if [ "$url" ]; then
        args="-O $name"
    else
        url="$name"
        name=$(basename "$name")
    fi
    if [ ! -e "$name" ]; then
        wget -O "$name" "$url"
    fi
}

main() {
    go get github.com/stevearc/pike
    pushd $(dirname $0) > /dev/null
    mkdir -p stiny/static/lib
    pushd stiny/static/lib > /dev/null
    if [ "$1" == "-r" ]; then
        rm -rf *
    fi

    dl http://code.angularjs.org/1.2.14/angular.min.js
    dl http://code.angularjs.org/1.2.14/angular-touch.min.js
    dl http://code.angularjs.org/1.2.14/angular-route.min.js
    dl https://angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.11.0.min.js
    dl https://raw.githubusercontent.com/ftlabs/fastclick/3497d2e92ccc8a959c7efb326c0fc437302d5bcf/lib/fastclick.js

    if [ ! -e bootstrap-3.1.1 ]; then
        dl https://github.com/twbs/bootstrap/archive/v3.1.1.zip
        unzip v3.1.1.zip
        rm v3.1.1.zip
        find bootstrap-3.1.1 -mindepth 1 -maxdepth 1 \( -not -name "fonts" -and -not -name "less" \) | xargs rm -r
    fi
    local fa_version=4.3.0
    if [ ! -e font-awesome-$fa_version ]; then
        dl http://fontawesome.io/assets/font-awesome-$fa_version.zip
        unzip font-awesome-$fa_version.zip
        rm font-awesome-$fa_version.zip
        find font-awesome-$fa_version -mindepth 1 -maxdepth 1 \( -not -name "fonts" -and -not -name "css" \) | xargs rm -r
    fi

    popd > /dev/null
    popd > /dev/null
}

main "$@"
