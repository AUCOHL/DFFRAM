# The nix-eda flake template
{
  inputs = {
    librelane.url = "github:librelane/librelane";
  };

  outputs = {
    self,
    librelane,
    ...
  }: {
    devShells = librelane.devShells;
  };
}
