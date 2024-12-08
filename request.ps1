# ocr_request.ps1

$uri = "http://localhost:25098/ocr"
$imagePath = "C:\temp\general_ocr_002.png"
$imageUrl = "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/general_ocr_002.png"

# Check and download image if not exists
if (-not (Test-Path $imagePath)) {
    Write-Host "Image not found, starting download..."
    Invoke-WebRequest -Uri $imageUrl -OutFile $imagePath
    Write-Host "Image download completed: $imagePath"
} else {
    Write-Host "Using existing image: $imagePath"
}

# Prepare request body
$body = @{
#    img_path = $imagePath
    img_url = $imageUrl
    cls = $true
} | ConvertTo-Json

# Set request headers
$headers = @{
    "Content-Type" = "application/json"
}

# Record start time
$startTime = Get-Date
# Send request
try {
    Write-Host "Starting OCR recognition..."
    $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -Headers $headers
    
    # Output results
    Write-Host "Recognition status: $($response.status)"
    Write-Host "Recognition results:"
    $response.result | ForEach-Object {
        $_ | ForEach-Object {
            Write-Host "Text: $($_.text)"
            Write-Host "Confidence: $($_.confidence)"
            Write-Host "Position: $($_.position)"
            Write-Host "------------------------"
        }
    }
}
catch {
    Write-Host "Error: $_"
}
finally {
    # Calculate and display time elapsed
    $endTime = Get-Date
    $duration = $endTime - $startTime
    Write-Host "Total time elapsed: $($duration.TotalSeconds) seconds"
}