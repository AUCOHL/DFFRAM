# The nix-eda flake template
{
  inputs = {
    librelane.url = "github:librelane/librelane/2.4.2";
  };

  outputs = {
    self,
    librelane,
    ...
  }: {
    devShells = librelane.devShells;
  };
}
