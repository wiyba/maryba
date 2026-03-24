{
  pkgs ? import <nixpkgs> { },
}:

let
  python = pkgs.python313.withPackages (ps: with ps; [
    fastapi
    uvicorn
    bcrypt
    jinja2
    python-multipart
    itsdangerous
    opencv4
    numpy
    libgpiod
  ]);
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    python
    ffmpeg
    proxmark3
  ];
}
