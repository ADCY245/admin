# Create necessary directories
$directories = @(
    "templates\user\products",
    "templates\user\profile",
    "templates\user\components",
    "templates\dealer\products",
    "templates\dealer\profile",
    "templates\dealer\components",
    "static\js\user",
    "static\js\dealer",
    "static\styles\user",
    "static\styles\dealer"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir"
    }
}

# Files to copy
$filesToCopy = @{
    # HTML files
    "templates\cart.html" = @("templates\user", "templates\dealer")
    "templates\company_selection.html" = @("templates\user", "templates\dealer")
    "templates\product_selection.html" = @("templates\user", "templates\dealer")
    "templates\quotation.html" = @("templates\user", "templates\dealer")
    "templates\profile\profile.html" = @("templates\user\profile", "templates\dealer\profile")
    "templates\products\blankets\blankets.html" = @("templates\user\products\blankets", "templates\dealer\products\blankets")
    "templates\products\chemicals\mpack.html" = @("templates\user\products\chemicals", "templates\dealer\products\chemicals")
    "templates\components\company_info.html" = @("templates\user\components", "templates\dealer\components")
    
    # JS files
    "static\js\blankets.js" = @("static\js\user", "static\js\dealer")
    "static\js\cart.js" = @("static\js\user", "static\js\dealer")
    "static\js\company_info.js" = @("static\js\user", "static\js\dealer")
    "static\js\company_selection.js" = @("static\js\user", "static\js\dealer")
    "static\js\mpack.js" = @("static\js\user", "static\js\dealer")
    "static\js\product_selection.js" = @("static\js\user", "static\js\dealer")
    "static\js\quotation.js" = @("static\js\user", "static\js\dealer")
    "static\js\selection.js" = @("static\js\user", "static\js\dealer")
    "static\js\dashboard.js" = @("static\js\user", "static\js\dealer")
}

# Copy files
foreach ($file in $filesToCopy.GetEnumerator()) {
    $source = $file.Key
    $destinations = $file.Value
    
    if (Test-Path $source) {
        foreach ($dest in $destinations) {
            $destFile = Join-Path $dest (Split-Path $source -Leaf)
            Copy-Item -Path $source -Destination $destFile -Force
            Write-Host "Copied $source to $destFile"
        }
    } else {
        Write-Host "Warning: Source file not found: $source"
    }
}

# Update template references
$templateDirs = @("templates\user", "templates\dealer")

foreach ($templateDir in $templateDirs) {
    $role = (Split-Path $templateDir -Leaf)
    
    Get-ChildItem -Path $templateDir -Recurse -Filter "*.html" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        
        # Update static file references
        $content = $content -replace 'href="/static/styles/', "href=`"/static/styles/$role/"
        $content = $content -replace 'src="/static/js/', "src=`"/static/js/$role/"
        
        # Update template extends and includes
        $content = $content -replace '{% extends "', "{% extends `"$role/"
        $content = $content -replace '{% include "', "{% include `"$role/"
        
        Set-Content -Path $_.FullName -Value $content -NoNewline
        Write-Host "Updated references in $($_.FullName)"
    }
}

Write-Host "File organization complete!"
