Start-Process -FilePath "python" -ArgumentList "-m trustrag.cli serve-api"
Start-Sleep -Seconds 3
Start-Process -FilePath "python" -ArgumentList "-m trustrag.cli serve-ui"
