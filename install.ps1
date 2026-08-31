#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Repo = "https://github.com/ensayiti/hermes-vacuum"
$Raw = "https://raw.githubusercontent.com/ensayiti/hermes-vacuum/main"
$Dest = "$env:LOCALAPPDATA\hermes\skills\productivity\hermes-vacuum"
$Tmp = "$env:TEMP\hermes-vacuum-install"

Write-Host "Installing hermes-vacuum to $Dest"

if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
if (Get-Command git -ErrorAction SilentlyContinue) {
  Write-Host "Cloning via git..."
  git clone --depth 1 $Repo $Tmp
} else {
  Write-Host "Downloading zip..."
  $Zip = "$env:TEMP\hermes-vacuum.zip"
  Invoke-WebRequest -Uri "$Repo/archive/refs/heads/main.zip" -OutFile $Zip
  Expand-Archive -Path $Zip -DestinationPath $Tmp -Force
  $Inner = Get-ChildItem $Tmp -Directory | Select-Object -First 1
  Move-Item "$($Inner.FullName)\*" $Tmp -Force
  Remove-Item $Zip -Force
}

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item -Path "$Tmp\*" -Destination $Dest -Recurse -Force
Remove-Item -Recurse -Force $Tmp

Write-Host "Installed. Verifying..."
hermes skills list | Select-String "vacuum"
Write-Host ""
Write-Host "Done. Restart hermes then run:"
Write-Host "  hermes"
Write-Host "  > /safe-cleanup dry-run"
