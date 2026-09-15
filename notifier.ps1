param (
    [string]$Title = "Fun Learning Kids",
    [string]$Message = "Notification",
    [string]$Type = "Info"
)

try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $templateType = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($templateType)
    $xml = [xml]$template.GetXml()
    $xml.GetElementsByTagName('text')[0].AppendChild($xml.CreateTextNode($Title)) | Out-Null
    $xml.GetElementsByTagName('text')[1].AppendChild($xml.CreateTextNode($Message)) | Out-Null
    
    $doc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $doc.LoadXml($xml.OuterXml)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($doc)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Fun Learning Kids").Show($toast)
    Write-Host "Notification sent successfully."
} catch {
    # Fallback to NotifyIcon balloon tip
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $balloon = New-Object System.Windows.Forms.NotifyIcon
        $balloon.Icon = [System.Drawing.SystemIcons]::Information
        $balloon.BalloonTipTitle = $Title
        $balloon.BalloonTipText = $Message
        $balloon.Visible = $true
        $balloon.ShowBalloonTip(5000)
        Start-Sleep -Seconds 1
        $balloon.Dispose()
        Write-Host "Balloon notification sent."
    } catch {
        Write-Host "Notification error: $_"
    }
}
