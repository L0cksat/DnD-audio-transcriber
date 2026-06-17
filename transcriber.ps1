Write-Host "================"
Write-Host "      MENU"
Write-Host "================"
Write-Host "1- PREPARE AUDIO"
Write-Host "2- TRANSCRIBE AUDIO"
Write-Host "3- EXIT"
Write-Host ""

function prepareAudio {
	$directory = Read-Host "PLEASE ENTER THE DIRECTORY."
	$parent = Split-Path -Path $directory -Parent
	$filename = Split-Path -Path $directory -Leaf
	if ($filename -match 'session_\d+'){
		$folderName = $Matches[0]
		Write-Output $folderName
	}else {
		$folderName = "session_$(Read-Host "PLEASE ENTER A NUMBER.")"
	}
	$outDir = "$parent\chunks\$folderName"
	New-Item -ItemType Directory -Path $outDir -Force
	ffmpeg -i "$directory" -f segment -segment_time 3600 -c copy "$outDir\chunk_%02d.mp3"
}

function transcribe {
	$chunksDir = Read-Host "PLEASE ENTER THE CHUNKS DIRECTORY."
	& "F:\MY PROJECTS REPOSITORIES\DnD-audio-transcriber\venv\Scripts\python.exe" "F:\MY PROJECTS REPOSITORIES\DnD-audio-transcriber\transcriber.py" $chunksDir
}

$choice = Read-Host "PLEASE CHOOSE AN OPTION"

while ($choice -ne "3"){
	
	if ($choice -eq "1"){
		prepareAudio
	}elseif ($choice -eq "2"){
		transcribe
	}else{
		Write-Host "PLEASE ENTER A NUMBER FROM 1 TO 3"
	}
$choice = Read-Host "PLEASE CHOOSE AN OPTION"
}

	


	