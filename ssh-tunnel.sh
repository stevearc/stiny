#!/bin/bash

main() {
    autossh -nNTy -i /home/pi/.ssh/id_rsa -R 9000:localhost:6543 pi@home.stevearc.com
}

main "$@"
