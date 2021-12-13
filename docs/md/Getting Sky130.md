# Getting Sky130
The best way to get it is via [Openlane](https://github.com/The-OpenROAD-Project/OpenLane): you clone that repo then run:

```sh
export PDK_ROOT=/usr/local/pdk
make pdk
```

Another option is to get a pre-built from https://github.com/Cloud-V/sky130-builds/releases: folow the instructions there.

I would really recommend adding whichever you exported as `PDK_ROOT` to your shell's profile.

## I don't have `realpath` on macOS!
`brew install coreutils`