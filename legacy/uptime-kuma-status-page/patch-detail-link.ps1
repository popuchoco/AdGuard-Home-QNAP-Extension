param([Parameter(Mandatory=$true)][string]$InputBundle,
      [Parameter(Mandatory=$true)][string]$OutputBundle,
      [string]$Slug = 'home-network')
$ErrorActionPreference = 'Stop'
$text = [IO.File]::ReadAllText($InputBundle)
$old = 's("li",null,[s("a",aie,[D(u,{icon:"info-circle"}),le(" "+d(e.$t("Help")),1)])])'
$new = 's("li",null,[s("a",{href:"/status/' + $Slug + '",class:"dropdown-item"},[D(u,{icon:"question-circle"}),le(" \u8a73\u7d30")])]),' + $old
if (-not $text.Contains($old)) { throw 'Expected Kuma menu fragment was not found; do not patch an unknown build.' }
$patched = $text.Replace($old, $new)
if (($patched.Length - $text.Length) -le 0) { throw 'Patch produced no insertion.' }
[IO.File]::WriteAllText($OutputBundle, $patched, [Text.UTF8Encoding]::new($false))
Write-Output $OutputBundle
