{
  description = "maryba";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems =
        f:
        nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (
          system: f nixpkgs.legacyPackages.${system}
        );
    in
    {
      packages = forAllSystems (
        pkgs:
        let
          python = pkgs.python313.withPackages (
            ps: with ps; [
              fastapi
              uvicorn
              bcrypt
              jinja2
              python-multipart
              itsdangerous
              opencv4
              numpy
              libgpiod
            ]
          );
        in
        {
          default = pkgs.writeShellScriptBin "maryba" ''
            export PATH="${
              pkgs.lib.makeBinPath [
                pkgs.ffmpeg
                pkgs.proxmark3
                pkgs.nftables
              ]
            }:$PATH"
            exec ${python}/bin/python ${self}/main.py "$@"
          '';
        }
      );
    };
}
