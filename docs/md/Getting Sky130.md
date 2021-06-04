# Getting Sky130
The best way to get it is via [Openlane](https://github.com/The-OpenROAD-Project/OpenLane): you clone that repo then run:

```sh
export PDK_ROOT=/usr/local/pdk
make pdk
```

Another option is to get a pre-built:

```sh
export PDK_ROOT=$(realpath ~/pdklite)
git clone --depth 1 https://github.com/olofk/pdklite $PDK_ROOT
```

I would really recommend adding whichever you exported as `PDK_ROOT` to your shell's profile.

## I don't have `realpath` on macOS!
`brew install coreutils`