# Create necessary directories
$directories = @(
    "templates\user\products\blankets",
    "templates\user\products\chemicals",
    "templates\user\components",
    "templates\user\profile",
    "templates\dealer\products\blankets",
    "templates\dealer\products\chemicals",
    "templates\dealer\components",
    "templates\dealer\profile",
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
    "cart.html" = @("templates\user", "templates\dealer")
    "company_selection.html" = @("templates\user", "templates\dealer")
    "product_selection.html" = @("templates\user", "templates\dealer")
    "quotation.html" = @("templates\user", "templates\dealer")
    "profile\profile.html" = @("templates\user\profile", "templates\dealer\profile")
    "products\blankets\blankets.html" = @("templates\user\products\blankets", "templates\dealer\products\blankets")
    "products\chemicals\mpack.html" = @("templates\user\products\chemicals", "templates\dealer\products\chemicals")
    "components\company_info.html" = @("templates\user\components", "templates\dealer\components")
    
    # JS files
    "js\blankets.js" = @("static\js\user", "static\js\dealer")
    "js\cart.js" = @("static\js\user", "static\js\dealer")
    "js\company_info.js" = @("static\js\user", "static\js\dealer")
    "js\company_selection.js" = @("static\js\user", "static\js\dealer")
    "js\mpack.js" = @("static\js\user", "static\js\dealer")
    "js\product_selection.js" = @("static\js\user", "static\js\dealer")
    "js\quotation.js" = @("static\js\user", "static\js\dealer")
    "js\selection.js" = @("static\js\user", "static\js\dealer")
    
    # CSS files
    "styles\login.css" = @("static\styles\user", "static\styles\dealer")
    "styles\signup.css" = @("static\styles\user", "static\styles\dealer")
    "styles\forgot-password.css" = @("static\styles\user", "static\styles\dealer")
    "styles\styles.css" = @("static\styles\user", "static\styles\dealer")
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
