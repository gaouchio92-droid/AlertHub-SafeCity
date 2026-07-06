Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$envFile = Join-Path $root ".env"

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing .env file at $envFile"
}

$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
if (-not (Test-Path -LiteralPath $docker)) {
    $docker = "docker"
}
else {
    $dockerBin = Split-Path -Parent $docker
    if (($env:PATH -split ";") -notcontains $dockerBin) {
        $env:PATH = "$dockerBin;$env:PATH"
    }
}

Push-Location $root
try {
    & $docker compose up -d --force-recreate backend nginx
    & $docker compose ps
    $diagnostics = Invoke-WebRequest -Uri "http://localhost/api/v1/connectors/diagnostics" -UseBasicParsing -TimeoutSec 20
    $diagnostics.Content
}
finally {
    Pop-Location
}
