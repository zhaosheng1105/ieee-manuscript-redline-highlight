# 运行环境、遥测与诊断

原生 API 调用无需启动整个 ROS 算法栈。只有请求涉及真值、速度、CAN 控制或规划器时，才进入对应集成层。

## 1. 三种接口分别负责什么

| 层次 | 入口 | 实际作用 |
|---|---|---|
| Autoverse 原生 | 官方 `avrs` / HTTP `/post` | 仿真对象、物理摩擦、位置、场景等 |
| 项目 ROS 2 | 节点参数、消息和服务 | 算法认为可用的能力、速度上限、规划与控制状态 |
| CAN / virtual CAN | 对应车辆与版本的 DBC 编码帧 | 持续驾驶指令、执行器与传感器反馈 |

`ggv_multiplier` 及 `grip_scale` 是本项目规划包络倍率；`SetFrictionModifiers` 改仿真物理缩放。`max_speed_mps=0` 是该规划栈的停车请求，不是 Autoverse 通用刹车 API。

对象别名 `ego`、车辆名 `eav24`、ROS namespace `/eav24` 是不同概念。先从当前对象列表、对象配置和图状态确认；保存配置中的默认输入模式不等于已核验的实时状态。

## 2. API 连接排查

1. 查实际 `avrs` 可执行文件、发行版本和源码位置。参考连接设置见[原生对照](native-cli-and-http.md)。读取配置时只提取所需 host/port，不复制无关凭据。
2. 确认访问的是用户希望操作的本机或远程仿真实例。`127.0.0.1` 在容器和宿主里指向不同网络空间。
3. 用 GetVersion 或对象列表做有超时的只读连接检查。HTTP 工具与 CLI 应指向同一 host/port。
4. 区分端口拒绝、权限阻塞、超时、HTTP 错误及应用响应错误。`ping` 输出“no”或CLI退出0均不足以解释根因。
5. 权限不足时保存实际错误及命令；不能将受限会话无网络/CAN/DDS权限解释为宿主没有运行仿真器，也不能换通道绕过明确访问限制。

只读查询失败时可以在修正地址、对象或环境后有限重试。写请求失败/超时先检查状态，确认是否已生效后再决定是否需要重发。不要自动重复 reset、restart 或 teleport。

## 3. ROS 2 真值与状态

先加载当前 ROS 环境及用户项目需要的消息类型，确认 domain、namespace、topic、类型与 QoS。下列变量为任务配置，不是本技能要求的固定值：

```bash
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 node list
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 topic list -t
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 topic info -v "$AV_TRUTH_TOPIC"
timeout 5s env ROS_DOMAIN_ID="$AV_DOMAIN" ros2 topic echo "$AV_TRUTH_TOPIC" --once --qos-reliability best_effort
timeout 5s env ROS_DOMAIN_ID="$AV_DOMAIN" ros2 topic hz "$AV_TRUTH_TOPIC"
```

使用前确认本机 CLI 支持相应选项。有限时长的 `timeout` 因到时退出，不自动表示话题故障；同时查看实际收到的样本。best-effort 是本案例传感器匹配方式，当前 publisher 的 QoS 优先。

判断顺序：发布者存在 → 接收新消息 → 类型/时间/单位有效 → 下游采用 → 实际效果。只列出 topic 不能证明有新帧，重复源时间戳不能刷新测量新鲜度。

本案例 `/eav24/ground_truth` 是 `geometry_msgs/msg/PoseStamped`，给位置与姿态，没有直接给速度、轮速或 RPM。项目用不同源时间戳的位姿求导估速；报告中应说“由位姿估计”，不要改称直接速度真值。

teleport/reset、时间倒退、长间隔后，清除旧差分历史和轨迹连续性，重新积累有效样本。复位跳跃不能算作车辆速度或累计行驶距离。

## 4. CAN 只读检查

```bash
ip -details link show dev "$AV_CAN0"
ip -details link show dev "$AV_CAN1"
timeout 5s candump -L "$AV_CAN1"
```

这些是系统/CAN 工具，不是 Autoverse CLI。总线可能承载大量数据，选择有限观察窗口与本任务需要的 ID；解析必须用当前 DBC，而非凭帧名猜比例系数。

本项目已用配置仅作示例：

| 总线 | ID / DLC | 含义 |
|---|---|---|
| vcan0 | 0x120 / 8 | 实际执行器反馈 |
| vcan0 | 0x141 / 7 | 轮速 |
| vcan0 | 0x211 / 8 | 转向 |
| vcan1 | 0x480、0x481 / 依DBC核对 | 前后轮温度 |

本案例温度每轮取 inner/center/outer 平均；接收线程轮询频率不等于温度实际更新频率。ROS Pose 使用米，配置文件里的出生位置可能为厘米；四元数求 yaw 常为弧度，teleport CLI yaw 为度，逐字段核对。

建立 vCAN、加载模块、改变接口或发送帧都是另有副作用的动作，不混在只读检查中。真实 `can0` 不能当 `vcan0` 使用。需要驾驶命令时先核对输入模式、DBC、周期、alive counter、使能及反馈，并确认唯一控制者；不提供脱离这些条件的裸 `cansend` 油门命令。

## 5. 坐标与传送

接口的坐标系、地图原点、规划坐标系和数据单位须分别确认。使用环境已有地标能减少错误高度，但地标存在也不代表与规划参考线完全重合。

本项目曾直接把 NED 真值当作规划 ENU，导致“出生在维修区”的错误判断；修正轴和原点后撤回了相关初始化改动。扩大轨迹对齐阈值无法修复坐标错误。

仅供 Yas North 旧项目复核的映射：

```text
x_plan = y_truth + 32.738037303 m
y_plan = x_truth + 123.821393749 m
yaw_plan = pi/2 + yaw_quaternion
```

其复现实验使用的反向传送构造为 `NED_X = y_plan − 123.821393749`、`NED_Y = x_plan − 32.738037303`、`yaw_deg = 90 − course_deg`。这组常数和四元数约定只来自该项目；换地图重新核对，不能因都是 NED/ENU 就照搬。

高程变化场景保留真实/已核验高度，不把旧赛道固定 Z 复制到新赛道。传送后读新鲜真值，比较位置、航向及轨迹关系；没有位姿源时只报告接口回执。

## 6. 现有 GGV 项目集成（有工程时才适用）

以下命令不包含在原生 CLI 中。本技能不分发这些脚本；仅在现场确有 `ggv_minimal` 且用户请求使用它时，在该目录运行。

```bash
./start_sim.sh --check
./start_sim.sh --self-test
./diagnose_sim.sh --domain "$AV_DOMAIN" --duration 8
./diagnose_sim.sh --host --domain "$AV_DOMAIN" --duration 8
```

`--check` 检查依赖，不发 CAN；`--self-test` 运行离线测试。诊断默认进入唯一匹配的已运行容器，不新建控制栈；`--host` 使用已配置的宿主 ROS 环境，duration 接受2–30秒。报告位于 `logs/diagnosis_*/report.json`。

本项目 launch 和部分诊断代码固定使用 `/eav24`，因此不能只替换 domain 就变成其他车辆的通用诊断器。

已授权启动或热调该算法栈时：

```bash
./start_sim.sh --state-source ground_truth --grip-scale 0.8 --max-speed 90
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 param get "$AV_BRIDGE_NODE" ggv_multiplier
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 param set "$AV_BRIDGE_NODE" ggv_multiplier 0.85
ROS_DOMAIN_ID="$AV_DOMAIN" ros2 param set "$AV_BRIDGE_NODE" max_speed_mps 0.0
```

`--max-speed` 单位 m/s，90只是原项目示例。参数读回后还须检查规划器实际使用值和真实响应；停车请求必须结合新鲜遥测确认速度降低，不能把“set成功”当车辆已停止。

`./thermal_grip.py` 也依赖原项目 DBC/配置。它持续写 `baseline_i × lookup(T_i)`，将覆盖手动摩擦设置；正常退出尝试恢复启动基线，但不主动停车。其状态 `verified` 表示该周期回读成功，`restored` 表示恢复已核验；强制退出或断连可能来不及恢复。

## 7. 故障定位速查

| 现象 | 优先核对 | 避免误判 |
|---|---|---|
| CLI无报错但值未变 | 应用响应、target、读回、其他写入者 | 不以退出0为成功 |
| 手动摩擦马上变回 | 温度适配器/自动采集器是否持续写 | 不反复与它抢写 |
| HTTP能连但ROS无数据 | 网络空间、domain、namespace、QoS、发布开关 | 不重装仿真器来修domain |
| topic存在但控制超时 | 实际新帧、源时间、必需CAN反馈 | 不只查topic名称 |
| reset回执成功但不能跟踪 | 坐标、原点、方向、高度、参考线、旧历史 | 不放大阈值掩盖错位 |
| 节点启动但车辆不动 | 输入模式、DBW/发动机、档位、CAN写入、执行器反馈 | 不把油门命令当真实移动 |
| 操作超时/断连 | 当前状态是否已改变、权限或服务状态 | 不无限重复写请求 |

优先停止本次失败的调用链并保留现场。需要恢复时只操作自己拥有的进程/控制器；不使用全局 `pkill` 或停止所有容器来排错。
