# Scope SCPI Automation Skeleton

這個專案現在已整理成可擴充的雛形，目標是讓後續 agent 可以在同一個架構上持續補品牌 profile 與控制功能。

目前已具備的基礎能力：

- `identify`
- `run`
- `stop`
- `capture`
- `channel on/off`
- `scale change`
- `time scale change`
- `measurement`
- `toggle sequence`
- `text/json logs`

## 目錄

```text
SKILL.md
scripts/
  scope_cli.py
  scope_core.py
  profile_loader.py
  logger.py
vendor_profiles/
  common.json
  keysight.json
  rigol.json
references/
  profile-spec.md
```

## 安裝

```powershell
pip install -r requirements.txt
```

## 列出可用 profile

```powershell
python .\scripts\scope_cli.py --list-profiles
```

## 列出 VISA resources

```powershell
python .\scripts\scope_cli.py --list --pyvisa-py
```

## 基本控制範例

辨識設備：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py identify
```

開啟 CH1：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py set-display --channel 1 --state on
```

設定 CH1 垂直檔位：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py set-scale --channel 1 --scale 0.5
```

`set-scale` 與 `set-time-scale` 現在會依照 profile 內的合法刻度規則自動 normalize，不是所有數值都會原樣送到示波器。
目前 `common` profile 使用 `1-2-5` decade sequence。

例如要求 `0.003` V/div，程式會自動套用最近的合法值，例如 `0.002` 或 `0.005`。

設定時間軸 scale：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py set-time-scale --scale 0.001
```

量測 CH1 Vpp：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py measure --channel 1 --item vpp
```

開始擷取：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py run
```

停止擷取：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py stop
```

截圖：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py capture --output .\captures\scope.png
```

執行 channel 切換序列：

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py toggle-sequence --channels 1,2,3,4 --scales 0.1,0.2,0.5,1.0 --interval 5 --cycles 1
```

## Logging

```powershell
python .\scripts\scope_cli.py --resource "TCPIP0::192.168.50.251::INSTR" --profile common --pyvisa-py --log-file .\logs\scope.log --json-log-file .\logs\result.json measure --channel 1 --item frequency
```

## 下一步建議

- 補更多品牌 profile
- 加入 auto-detect profile
- 擴充更多 capture 品牌支援
- 用 skill workflow 封裝成 agent 可直接呼叫的任務
