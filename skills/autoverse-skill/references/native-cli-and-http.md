# Autoverse 原生 CLI 与 HTTP 调用参考

## 证据范围与版本

本参考核对于 2026-11-09，依据本机已安装 `autoverse-cli 0.28.2` 的 Python 源码、CLI help、项目调用代码及既有日志。此次编写没有连接运行中的仿真，也没有重新执行控制命令。

- CLI 版本：`avrs --version` 返回 `0.28.2`；发行包名是 `autoverse-cli`，导入包名是 `avrs`。
- 仿真安装包：本机验证清单记录 `0.36.2`、`a2rl-humble`；它不是此次查询的在线仿真版本。
- 仿真版本和 CLI 版本独立；换机器或升级后以本地实际帮助/源码及在线 `get-sim-version` 为准。
- 标记 **项目使用**：本项目代码存在实际调用，部分还保存读回/运行日志；不是每个变体都在线验证过。
- 标记 **源码确认**：参数与请求体由 0.28.2 源码确认，本次不声称已有项目成功执行记录。
- 未发现独立的官方 Python SDK 发行包。下文是官方 CLI 的 HTTP 协议及标准库直连方式，不把项目封装称为官方 SDK。

本机定位示例，迁移后重新发现，不要求其他机器具有这些路径：

```text
CLI: /home/automan/anaconda3/envs/avrs/bin/avrs
Python: /home/automan/anaconda3/envs/avrs/bin/python
源码: /home/automan/anaconda3/envs/avrs/lib/python3.10/site-packages/avrs/
仿真: /home/automan/Projects/a2rl/autoverse-linux-0.36.2-official/Linux/
```

## 发现命令与连接目标

```bash
command -v avrs
avrs --version
avrs --help
avrs vd --help
avrs teleport --help
avrs can-tool echo --help
```

原生 `avrs` 没有通用 `--host`、`--port`、`--timeout` 参数。旧 HTTP 控制 API 按以下规则确定连接：

| 设置 | 原生 CLI 0.28.2 行为 |
|---|---|
| 主机 | 环境变量 `AVRS_SIM_ADDRESS` 优先，其次 CLI 配置中的 `sim_address`，最后 `localhost` |
| 端口 | CLI 配置中的 `sim_api_port`，否则 `30313` |
| 配置文件 | `~/.config/avrs/config.json` |
| HTTP | `POST /post`，`Content-Type: application/json` |
| 超时 | 单次 HTTP 连接使用 10 秒 |
| 执行方式 | 同步阻塞；收到响应后原样打印响应文本 |

```bash
AVRS_SIM_ADDRESS=127.0.0.1 avrs get-sim-version
```

需要改端口时，优先用本 skill 薄客户端显式传参；若确实修改 CLI 配置，只合并目标键并保留其他现有设置，不覆盖整份配置。无需读取或输出许可、云账户等无关字段。

`avrs --help`/`--version` 并非绝对无副作用：主程序先初始化日志、加载配置目录，并调用 `check_app_is_latest()`，然后才解析参数。当前 0.28.2 的该检查函数是 `pass`，没有实际联网；其他版本需检查实现，不能推断永久不联网。初始化可能创建/写入 `~/.config/avrs/` 日志。要求严格离线或不写配置目录时，优先读 `avrs/avrs.py`、`app_version.py` 和 `requests/*.py`；包版本也可用 `importlib.metadata.version('autoverse-cli')` 读取。

## 只读查询

以下为**源码确认**；摩擦读取另有**项目使用**记录。表中目标是信封的 `TargetObjectId`，数字 `0`、空字符串 `""` 和对象名称不要互换。

| 原生命令 | RequestType | 目标 | RequestBody |
|---|---|---|---|
| `avrs get-sim-version` | `GetVersion` | `0` | `{}` |
| `avrs ping` | `GetVersion` | `0` | `{}` |
| `avrs get-session-id` | `GetSessionId` | `0` | `{}` |
| `avrs list-sim-objects` | `ListSimObjects` | `0` | `{"bVerbose":false,"bListComponents":false,"isolate":""}` |
| `avrs get-object-config --target ego` | `GetObjectConfig` | `"ego"` | `{}` |
| `avrs dump-sim-config` | `DumpSimConfig` | `""` | `{}` |
| `avrs environment get-meta` | `GetEnvironmentMeta` | `""` | `{}` |
| `avrs vd get-friction-modifier All --object-name ego` | `GetFrictionModifiers` | `"ego"` | `{"Tires":"All"}` |

`list-sim-objects` 支持 `-v`、`--components`、`--isolate NAME`，分别填充上表三个 body 字段。全局 `avrs --verbose ...` 控制信封的 `bVerboseResponse`，与 `list-sim-objects -v` 不是同一个字段。

`get-object-config` 使用 `--target`；不能统一改成 `--object-name`。查询对象列表后使用实际名称，不能把 ROS namespace（如 `eav24`）直接等同于 API 对象（本项目通常为 `ego`）。

本版本没有在 CLI 中发现独立的 `GetState`、`GetPose`、`GetLandmarks` 或 `set-temperature` 命令。需要速度/位姿/胎温时使用当前工程的遥测或 CAN/ROS；需要地标时读当前环境配置的 `landmarks`，并与 `environment get-meta` 提供的信息核对。不臆造 HTTP 请求类型。

`ping` 会捕获异常并打印 `no`，退出码可能仍为 0。它不能仅凭退出码作为连接成功证据。

## 摩擦倍率：项目使用

```bash
avrs vd get-friction-modifier All --object-name ego
avrs vd set-friction-modifier 0.90 All --object-name ego
avrs vd set-friction-modifier 0.85 RR --object-name ego
avrs vd get-friction-modifier All --object-name ego
```

轮胎选择严格为 `FL FR RL RR F R All`，区分大小写。倍率为无量纲缩放，CLI 帮助说明 0 表示无抓地；项目适配器为自身实验另加了“有限正值”的检查，不应误称为官方接口的全部合法范围。

- 读取：`GetFrictionModifiers`，body `{"Tires":"All"}`。
- 设置：`SetFrictionModifiers`，body `{"NewModifier":0.9,"Tires":"All"}`。
- 本项目常见 ACK：`New Friction scaling has been set for the specified tires`。
- 四轮读回类似 `FL: 1.000000`、`FR: 1.000000`、`RL: 1.000000`、`RR: 1.000000`，可能包在 JSON 字符串内。
- 设置后读回四轮，以请求的轮组和数值验证。多轮分次修改不是原子操作；失败时可能已有部分轮胎生效。
- 物理摩擦倍率与规划器 GGV 倍率分别记录。等效温度标签经查表得到倍率，不等于给仿真胎温直接赋值。

## 回正、地标移动和瞬移：项目使用

```bash
avrs reset-to-track --object-name ego
avrs move-to-landmark MvStart0 --object-name ego
avrs teleport 100 200 -1 --frame ned --yaw 90 --object-name ego
```

这些是互相独立的语法示例，坐标和地标需由当前环境确定，不将示例坐标直接用于未知赛道。

| 命令 | RequestType | RequestBody |
|---|---|---|
| `reset-to-track` | `ResetToTrack` | `{}` |
| `move-to-landmark NAME` | `MoveToLandmark` | `{"LandmarkName":"NAME"}` |
| `teleport X Y Z --frame ned --yaw DEG` | `Teleport` | `{"X":X,"Y":Y,"Z":Z,"yaw":DEG,"NavFrame":"ned"}` |

以上目标均由 `--object-name` 设置。原生 `move-to-landmark` 默认 `Ego`，另外两项默认 `ego`；实际调用显式给对象名称，避免依赖大小写默认值。

`teleport` 的 NED 位置单位为米；`--yaw` 单位为度，0 指北、顺时针为正。`--frame` 只接受 `ned` 或 `LLA`；LLA 时 X/Y/Z 对应纬度/经度/高度，源码帮助没有进一步声明垂直基准，应查当前环境定义。不能直接把规划轨迹 ENU 坐标或弧度航向作为这些参数。

`reset-to-track` 意图是移动到最近赛道点并沿赛道方向摆正；它不是清除所有隐藏物理状态。ACK 后仍需使用位姿、速度、轨迹距离核对恢复结果。

## 环境、输入、旗帜和显示：源码确认

| 原生命令 | RequestType / 目标 | RequestBody |
|---|---|---|
| `avrs set-environment NAME` | `SetEnvironment` / `""` | `{"newEnvironmentName":"NAME"}` |
| `avrs environment set-time-of-day 14` | `SetTimeOfDay` / `""` | `{"TimeOfDay":14.0}` |
| `avrs configure-vehicle-input CAN` | `ConfigureVehicleInput` / `"Ego"` | `{"InputMode":"CAN"}` |
| `avrs change-camera ego` | `ChangeCamera` / `""` | `{"pixelStreamObjectId":"ego","bActivatePixelStream":false}` |
| `avrs toggle-hud` | `ToggleHud` / `"Ego"` | `{}` |
| `avrs set-lod 1` | `ConfigureSimLod` / `"lodctrl"` | `{"newLod":1}` |
| `avrs restart` | `RestartSimulation` / `0` | `{}` |
| `avrs exit-sim` | `ExitSim` / `0` | `{}` |

`set-time-of-day` 的帮助范围为 0–24 小时；`set-lod` 帮助定义 0 为最高细节、1 为最低细节。`set-environment` 使用环境名字，不是环境 JSON 路径；切换后重新核实环境与对象。

`configure-vehicle-input` 只接受 `None Keyboard WheelAndPedals CAN`，CLI 没有 `--object-name`。`change-camera` 的对象是位置参数，`--activate-pixel-stream` 将对应 body 布尔字段置 true。`toggle-hud` 为切换操作，没有幂等的“设为打开”参数。

旗帜设置语法：

```bash
avrs race-control --session-type SESSION_ID --track-flag TRACK_ID \
  --car-flag CAR_ID --sector-flag SECTOR1_ID SECTOR2_ID SECTOR3_ID \
  --object-name ego
```

替换为已核对的整数。HTTP 类型 `RaceControl`，目标为对象，body 为 `{"sessionType":...,"trackFlag":...,"carFlag":...,"sectorFlag":[...,...,...]}`。未给的参数默认 -1；`--sector-flag` 必须恰好 3 个整数。此 CLI 源码不定义旗帜编号含义，不推测“绿旗”等对应数字。

## 其他已发现命令族：按需读帮助

下列为**源码确认**，不要据此声称项目验证了全部行为。

- `avrs scenario start NAME` / `avrs scenario stop`：`ScenarioControl`、目标 `""`，body 分别为 `{"scenarioName":"NAME","action":"start"}` / `{"action":"stop"}`。
- `avrs spawn-object SPEC LANDMARK --object-type Eav24 --name-override NAME`：`SpawnObject`、目标 `0`；body 含 `name,type,spec,bUseStoredInitializer:true,location:{},rotation:{},landmark,payloads:[]`。
- `avrs vehicle-replay start-recording FILE --object-name ego --rate-hz 100 --not-single-lap`；停止为 `stop-recording --object-name ego`。涉及 `ConfigureVehicleReplay` 的完整 body 较长，使用原生 CLI 或先读对应源码，不只猜一个 `recordAction` 就代替所有配置。
- `avrs vehicle-replay spawn PROFILE`、`spawn-group GROUP`、`despawn --name NAME`；各参数读该子命令 help。`despawn --all` 删除所有 replay/NPC 对象，不作为默认清理步骤。
- `avrs lwi start-log FILE --format csv --rate-hz 100`、`stop-log`、`get-times`：轻量接口日志；与 ROS bag 不是同一个记录器。
- `avrs log-path FILE SECONDS`：路径日志；`SECONDS=-1` 持续到仿真结束，另有 `--filepath ABSOLUTE_PATH`。
- `avrs inject-fault gnss|imu|lidar|can ...`：故障注入。常用 `--target`、`--duration`、`--dropout`、`--freeze`；0 时长表示持续。先核对传感器特定参数及单位。
- `avrs leaderboard ...`：计时/圈数/显示；`launcher ...`：安装、下载与许可；`race-cloud ...`：云端功能。它们不是单次本地控制的必要依赖。
- `avrs sim-config compare-configs A B` 读取比较配置；`apply-preset {default,lightweight,a2rl} --sim-path PATH` 修改安装配置，不能用于只读发现。

`npc.py` 虽存在于包内，但 `avrs.py` 中 `Npc(sps,cfg)` 被注释，当前 root help 没有 `npc` 命令。不要把“源码文件存在”直接等同于“CLI 已注册可用”。

## CAN 命令与 HTTP 的边界

`can-tool` 使用 SocketCAN，不走 `/post`。可读取已存在虚拟接口；本 skill 不将任意真实 CAN 设备当作本地仿真接口。

```bash
avrs can-tool list-dbc
avrs can-tool echo vcan0 vcan1 --dbc_names CACHED_DBC_NAME --duration 2
avrs can-tool echo vcan1 --dbc_names CACHED_DBC_NAME --isolate SIGNAL_NAME --duration 2
```

`echo` 支持 `--rates` 和 `--save-report-as FILE`；缓存 DBC 通过 `add-dbc PATH [--overwrite-ok]` 添加。0.28.2 `get_dbcs()` 的直接文件路径分支加载后未加入返回列表，存在实现缺陷，不能仅依 help 假定任意路径都可用；优先已有缓存并核对实际输出。

存在 `can-tool send-eav24-input CAN_NAME DBC_NAME --throttle V --gear N --brake V --steer V --duration S`。帮助称 throttle/brake 0–1、steer -24–24，但实现直接将值写入 `HL_TargetThrottle`、四轮 `HL_TargetPressure_*` 和 `HL_TargetPSAControl`，没有归一化转换。必须以所用 DBC 的量纲和车辆输入约定为准；不能把该帮助范围当成跨版本控制单位，更不能在已有控制器同时发命令时盲发。

## HTTP 完整信封和薄客户端

下面是完整的读取请求，可保存为 `read-friction.json`：

```json
{
  "TargetObjectId": "ego",
  "RequestType": "GetFrictionModifiers",
  "bVerboseResponse": false,
  "RequestBody": {"Tires": "All"}
}
```

在 skill 目录执行，先检查请求，再按任务范围发送：

```bash
python3 scripts/avrs_http.py --host 127.0.0.1 --port 30313 --timeout 3 \
  --request-file read-friction.json --dry-run
python3 scripts/avrs_http.py --host 127.0.0.1 --port 30313 --timeout 3 \
  --request-file read-friction.json --response-file read-friction-response.txt
```

也可由 stdin 提供完整 JSON，`--request-file -`：

```bash
python3 scripts/avrs_http.py --host 127.0.0.1 --port 30313 --timeout 3 \
  --request-file - --dry-run <<'JSON'
{"TargetObjectId":"ego","RequestType":"SetFrictionModifiers","bVerboseResponse":false,"RequestBody":{"NewModifier":0.9,"Tires":"All"}}
JSON
```

该 helper 是标准库 HTTP 薄传输：不读取 `avrs` 配置，不自动重试，不做仿真语义成功确认。显式给 host/port；`--dry-run` 仅展示请求，不发送。`--response-file` 保存响应供后续核查。完成动作应由 API 专属 ACK/读回/遥测证据判定，不能仅依据 helper 的退出码。

官方 CLI 的旧 HTTP 与另一个 `describe-app` 命令不要混用：0.28.2 的 `describe-app` 走硬编码 `0.0.0.0:51111`、`GET /api/v1.0/describe-app`；其源码没有启用 `AVRS_SIM_ADDRESS`/CLI 配置覆盖。这不是旧 `/post` 接口的替代端点。

## 返回值与执行核查

1. 保留 HTTP 状态和原始响应；JSON 解析成功时也保留原文。结果可能是纯字符串、对象或包裹字符串的 JSON。
2. 官方 CLI 收到非 200 也可能只打印提示，不抛出异常；退出码 0 不等于仿真接受命令。
3. 对摩擦使用 ACK 与四轮读回；对传送/回正核对位姿与速度；对环境切换重新查询环境 metadata；没有可靠读回时说明“已发送/收到 ACK”及未验证的部分。
4. 请求超时可能表示服务端已执行但响应未到。先读状态再决定下一步，特别是切换、重启、spawn、toggle，不能无条件重发。
5. 不用一个泛化 `success` 字段解释所有接口；已核实源码没有给出统一响应 schema。

## 源码与历史证据定位

官方包内相对路径：`requests/request.py:17–61`（信封/连接），`cfg.py`（配置路径），`avrs.py`（注册/初始化），`app_version.py`（版本与检查函数），`requests/vd.py`、`teleport.py`、`reset_to_track.py`、`move_to_landmark.py`、`environment.py`、`misc.py`、`list_sim_objects.py`、`get_object_config.py`、`vehicle_input.py`、`race_control.py`、`change_camera.py`、`rest_request.py`。

项目内相对路径：

- `ggv_minimal/src/ggv_sim/ggv_sim/thermal_grip.py`：同步 HTTP、ACK、四轮解析与读回。
- `ggv_minimal/src/ggv_sim/ggv_sim/thermal_standalone.py`：原生 CLI 封装、温度监听及响应解包。
- `ggv_minimal/wm_pipeline/comparison/collect_recovery.py`：地标回位与 NED 瞬移调用。
- `ggv_minimal/tools/collect_data.py`：`reset-to-track` 调用及采集流程。
- `ggv_minimal/data/live_ggv_20261103T043059_405973Z/recorder.log`：摩擦前后读回的既有日志。
- 本机 `autoverse-linux-0.36.2-official.verification.json`：安装包版本证据；不把里面的历史 `runtime_started` 当成当前进程状态。

新项目只需新的连接目标、对象名和当前版本证据即可使用本参考；上述历史项目不是运行依赖。
