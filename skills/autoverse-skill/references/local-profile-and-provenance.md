# 本机参考、迁移与来源

本文件提供线索，不将旧配置当作当前现场事实。只读核查日期：2026-11-09。原项目文件和官方软件均不随 skill 分发；调用知识、请求示例和 HTTP 工具可独立使用。

## 已知本机配置

| 项目 | 历史/本地值 | 使用前核对 |
|---|---|---|
| 仿真安装 | `~/Projects/a2rl/autoverse-linux-0.36.2-official` | 当前实际进程/包版本 |
| CLI | `~/anaconda3/envs/avrs/bin/avrs` | PATH、发行版、源码/帮助 |
| CLI发行包 | `autoverse-cli 0.28.2` | 与仿真版本分别记录 |
| CLI源码 | avrs 环境的 `lib/python3.10/site-packages/avrs/` | 实际Python环境，不强依赖该绝对目录 |
| 旧HTTP API | 本机 `127.0.0.1:30313`、`POST /post` | CLI配置/环境变量/容器网络 |
| API目标 | `ego` | 当前对象列表；大小写和别名支持 |
| 车辆及ROS | `eav24`、`/eav24`、domain 78 | API target 与ROS namespace分别检查 |
| CAN | `vcan0`、`vcan1`，2026 DBC | 当前车辆配置和接口类型 |
| 真值 | `/eav24/ground_truth`，PoseStamped | 发布开关、类型、QoS及新帧 |

发现配置后可在用户当前项目记录 host、port、对象、环境、遥测来源和所有者；后续同一会话沿用仍有效信息。不要为小查询强制创建 profile，也不要把别人机器的地址写入共享 skill。

## 证据等级

- **官方源码支持**：已安装 CLI 中有相应解析与请求构造，说明该客户端的调用方式。
- **项目历史实跑**：旧记录包含回执、参数读回或位姿核验，说明当时现场执行过。
- **本包离线验证**：请求封包、错误处理与mock响应通过测试，不证明此刻能连接仿真器。
- **本轮现场验证**：只有本次实际请求并核验的结果才这样报告。

制作本 skill 时没有发送仿真控制请求。旧文档中的“当时尚未验证”与后续成功记录按日期和对象分别理解，不能互相覆盖成一个笼统状态。

## 官方与项目来源

官方路径以 `avrs/` 软件包根目录为基准：

- `requests/request.py`：HTTP 信封、POST /post、默认端口、10秒超时及 CLI 配置覆盖。
- `avrs.py`、`cfg.py`、`app_version.py`：命令注册、配置路径、版本及更新检查。
- `requests/misc.py`、`list_sim_objects.py`、`get_object_config.py`：版本、会话、对象查询。
- `requests/vd.py`：摩擦及车辆动力学命令、轮胎选择器。
- `requests/reset_to_track.py`、`move_to_landmark.py`、`teleport.py`：位置控制与字段/单位。
- `requests/environment.py`、`vehicle_input.py`、`race_control.py`：环境、输入模式与旗号字段。

原工作区相对路径，供必要时追溯：

| 内容 | 来源 |
|---|---|
| 实际摩擦HTTP与读回解析 | `ggv_minimal/src/ggv_sim/ggv_sim/thermal_grip.py:28` |
| 原生CLI参数顺序、逐轮基线与恢复 | `ggv_minimal/src/ggv_sim/ggv_sim/thermal_standalone.py:22`、`:151`、`:168` |
| 摩擦请求/读回相符历史 | `ggv_minimal/logs/thermal_20261102_141455_003248/thermal_grip.jsonl:4` |
| 实际reset回执 | `ggv_minimal/data/wm_boundary_bank_20261103/events.jsonl:308` |
| 地标、传送与位姿核验历史 | `ggv_minimal/data/wm_m5_eval_b3_fixed_T70_20261103_v2/events.jsonl:4`、`:5`、`:7` |
| 传送构造与反向坐标映射 | `ggv_minimal/wm_pipeline/comparison/collect.py:37` |
| 坐标错误与已撤回假说 | `ggv_minimal/STARTUP_FIXES.md:3` |
| 规划倍率/物理摩擦分离 | `ggv_minimal/README.md:45` |
| 诊断/停车/恢复 | `ggv_minimal/tools/diagnose.py`、`tools/collect_data.py:431`、`:555` |
| 控制权与vCAN限制 | `ggv_minimal/src/ggv_sim/ggv_sim/bridge.py:192`、`codec.py:83` |

## 在其他项目复用

1. 保留整个 `autoverse-skill/` 文件夹，确保 SKILL.md 能找到 references、scripts 和请求样例。
2. 让执行者读 SKILL.md，并提供此次动作；只有未知的目标地址/对象/坐标等才需补充。
3. 有 `avrs` 时优先核对当前版本后直接调用；无 CLI 但有原生 HTTP API 时，使用包内标准库工具。
4. 需要速度/温度/位姿核验时，使用当前项目实际提供的遥测入口；没有就标明验证缺口，不复制旧ROS节点当通用接口。

未来发现新命令，将其准确语法、请求结构、版本和读回方式补入原生手册；先区别源码支持与真实调用证据。维护时保留用户新增内容，不用旧项目的发布副本覆盖较新的个人安装版。
