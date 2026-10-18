param([Parameter(Mandatory=$true)][string]$FixturePath)
$ErrorActionPreference = 'Stop'
$fixtures = Get-Content -LiteralPath $FixturePath -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($fixture in $fixtures) {
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($fixture.command, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count -ne 0) { throw "Parse failed for $($fixture.cwd): $($parseErrors.Message -join '; ')" }
    $commands = @($ast.FindAll({param($node) $node -is [System.Management.Automation.Language.CommandAst]}, $true))
    if ($commands.Count -ne 1) { throw 'Generated guidance did not parse as exactly one command' }
    $elements = $commands[0].CommandElements
    $cwdIndex = -1
    for ($i = 0; $i -lt $elements.Count; $i++) {
        if ($elements[$i].Extent.Text -eq '--cwd') { $cwdIndex = $i + 1; break }
    }
    if ($cwdIndex -lt 0 -or $cwdIndex -ge $elements.Count) { throw 'Missing cwd argument' }
    $argument = $elements[$cwdIndex]
    if ($argument -isnot [System.Management.Automation.Language.StringConstantExpressionAst] -or
        $argument.StringConstantType -ne 'SingleQuoted' -or $argument.Value -cne $fixture.cwd) {
        throw "Cwd did not remain exactly one unchanged literal: $($fixture.cwd)"
    }
    $utf8Hex = [Convert]::ToHexString([Text.Encoding]::UTF8.GetBytes($argument.Value))
    [Console]::WriteLine("PARSER_ONLY_LITERAL_OK cwd_utf8_hex=$utf8Hex")
}
[Console]::WriteLine("PARSER_ONLY_PASS $($fixtures.Count); no command invoked")
