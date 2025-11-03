# Поиск всех возможных путей к python.exe
$paths = @(
    "$env:LOCALAPPDATA\Programs\Python\",
    "C:\Program Files\Python\",
    "C:\Program Files (x86)\Python\",
    "$env:USERPROFILE\AppData\Local\Programs\Python\"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        $pythonExe = Get-ChildItem -Path $path -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
        if ($pythonExe) {
            Write-Output "Найден Python: $pythonExe"
            exit 0
        }
    }
}

Write-Output "Python не найден"
exit 1
