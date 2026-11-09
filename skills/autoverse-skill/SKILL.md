---
name: autoverse-skill
description: 查询和控制 Autoverse 仿真器的原生 avrs CLI / HTTP 接口，复用轮胎物理摩擦读写、回到赛道、地标移动、坐标传送、环境及输入模式等调用方式，并验证读回。用于“调用Autoverse接口”“改轮胎摩擦”“复位/teleport”“查询仿真对象”等请求；需要ROS/CAN联调时区分项目桥接参数与原生物理接口。可作为独立技能包使用，不依赖thermal_tire_ggv工程。
metadata:
  version: "0.1.0"
---

# Autoverse 接口调用

把用户的短指令转换成当前仿真实例上的准确接口调用，完成请求、读回和效果核对。优先使用官方 `avrs`；需要轻量脚本或没有安装该 CLI 时，可使用包内标准库 HTTP 工具。无需启动完整科研项目流程。

本技能来自 `thermal_tire_ggv` 的实际接口调用和本机官方 CLI 源码核查。参考基线为 **Autoverse 仿真包 0.36.2、autoverse-cli 0.28.2**；两者是不同组件的版本，不要求版本号相同。新环境先核对实际版本和接口，不把本地支持列表当作所有版本的保证。

## 先定位本次操作

1. 从当前对话、运行记录和本地配置确定目标实例、车辆对象、用户要改变的量及预期效果。只查缺失项，不让用户重复已提供信息。
2. 核对 CLI 路径与连接地址。`avrs` 不在 PATH 时检查已有环境；本机历史路径为 `~/anaconda3/envs/avrs/bin/avrs`。不要自动升级/重装工具或改全局配置。
3. 用已知只读请求确认连接和对象，随后进入相关操作手册。CLI 退出码、HTTP 200 和接口 ACK 均不能单独证明控制效果成立。
4. 已明确请求的运行时设置直接在授权范围内执行；遇到影响正确性的歧义只澄清该项。例如“抓地倍率”可能指物理摩擦或规划包络，不能猜测并同时改两者。
5. 保存必要的请求/回执，完成后报告目标、实际结果和仍未核验的内容。小查询只需简短输出，不强制建立实验目录。

## 按任务读取

| 任务 | 参考 |
|---|---|
| CLI 语法、HTTP 请求类型、连接配置、对象/环境/输入模式等 | [原生 CLI 与 HTTP 对照](references/native-cli-and-http.md) |
| 改四轮/单轮摩擦、临时修改与恢复、复位、地标、传送 | [直接操作配方](references/operation-recipes.md) |
| 连接失败、ROS/CAN、真值、速度、坐标、控制器争用 | [运行环境与诊断](references/runtime-and-troubleshooting.md) |
| 当前机器的已知路径、历史调用证据、迁移到其他项目 | [本机参考与来源](references/local-profile-and-provenance.md) |

进入具体任务时读取相应手册即可，不遍历整个旧项目。完整包自包含；旧项目路径仅用于进一步溯源。

## 常用原生命令

下列 `AVRS`、`AV_OBJECT` 是示例 shell 变量，不是官方环境变量。先替换为已确认的工具和对象；`ego` 是本项目使用的目标别名，不等同于 ROS 命名空间 `eav24`。

```bash
AVRS=avrs
AV_OBJECT=ego

"$AVRS" get-sim-version
"$AVRS" list-sim-objects
"$AVRS" get-object-config --target "$AV_OBJECT"
"$AVRS" vd get-friction-modifier All --object-name "$AV_OBJECT"
```

用户要求设置摩擦时，保存原四轮值，执行设置，再核对四轮读回：

```bash
"$AVRS" vd set-friction-modifier 0.9 All --object-name "$AV_OBJECT"
"$AVRS" vd get-friction-modifier All --object-name "$AV_OBJECT"
```

`0.9` 是示例无量纲物理摩擦缩放值，不是已测得的路面摩擦系数，也不改变项目的规划 `grip_scale`。单轮/异值设置、恢复和核验见操作配方。

```bash
"$AVRS" reset-to-track --object-name "$AV_OBJECT"
"$AVRS" move-to-landmark MvStart0 --object-name "$AV_OBJECT"
"$AVRS" teleport "$AV_X" "$AV_Y" "$AV_Z" --frame ned --yaw "$AV_YAW_DEG" --object-name "$AV_OBJECT"
```

最后三条是位置修改，只在请求相应动作时调用。地标必须存在；坐标与高度来自当前环境。NED 用米，yaw 用度，正北为 0、顺时针为正；不要把旧赛道 ENU 坐标直接填入。

## 包内 HTTP 工具

`scripts/avrs_http.py` 是标准库薄客户端，支持 Python 3，无 ROS、官方 Python 包或原项目依赖。它读取完整原生请求 JSON，发送一次 `POST /post`；不自动重试，也不读取或修改 `avrs` 全局配置。

在 skill 目录中：

```bash
# 仅预览，不连接
python3 scripts/avrs_http.py --request-file assets/get-version.json --host 127.0.0.1 --port 30313 --dry-run

# 实际只读查询
python3 scripts/avrs_http.py --request-file assets/get-version.json --host 127.0.0.1 --port 30313
python3 scripts/avrs_http.py --request-file assets/get-friction-ego.json --host 127.0.0.1 --port 30313
```

`get-friction-ego.json` 仅适用于已确认的 `ego` 对象；其他对象在任务目录生成对应请求，不修改共享示例。完整信封、写请求和响应解释见原生对照表。`--request-file -` 接受标准输入，`--response-file PATH` 可保留原始回执，`--timeout` 单位为秒。

工具成功退出只表示 HTTP 传输完成；仍需解释应用响应并做针对性读回。dry-run 和本包的模拟测试不等于现场接口验证。

## 调用中的关键约定

- **对象与连接明确。** CLI 连接配置和显式 HTTP host/port 可能不同；不要在两个实例之间误读回。API target、车辆配置名和 ROS namespace 分别核对。
- **一个通道一个写入者。** 持续温度适配器、采集器或控制栈可能覆盖手动请求；先识别当前所有者，不能杀掉未知进程来抢控制。
- **修改后看实际值。** 摩擦核对四轮；复位/传送核对位姿；输入模式/环境核对实际响应和可用状态。没有对应状态源时，准确报告仅收到回执，不声称实测验证完成。
- **恢复取决于任务。** 临时试验恢复先前读到的各轮值；用户要求保持新设值时保留该设置。不要一律恢复 1.0，也不要将上一周期结果继续累乘。
- **超时意味着结果可能未知。** 写请求超时后先查询当前状态，不能认定未执行并连续重发；未知状态或反复失败时停止本次重试并报告。
- **单次调用不扩展成自动驾驶。** 查询对象不顺带重启场景；修改摩擦不顺带改规划器；传送不顺带启动旧实验。加载本技能不继承原项目历史采集授权。
- **运行时 API 与文件修改分开。** 用户要求临时设置不代表可以改模拟器安装、车辆 JSON、DBC 或原始算法库。真实硬件 CAN 也不属于默认仿真调用范围。

## 直接理解这些短请求

- “看一下四个轮胎当前倍率”：get 四轮并解析返回，不写值。
- “把 ego 四轮物理摩擦设成 0.9”：保存当前值、set All、get 比较；最终保持 0.9。
- “临时把右后轮降到 0.8，结束后恢复”：记录右后轮原值，执行有边界的任务，再恢复并读回；需有明确结束条件。
- “车滑出去了，放回赛道”：依据当前控制状态协调复位，调用 reset-to-track 并检查实际位置；只管理本次拥有的控制栈。
- “传送到这个 NED 点”：核对米/度/高度及所选对象，teleport 后检查新位姿。
- “读车速/轮胎温度”：检查当前已有遥测，按 ROS/CAN 路由；不编造 `GetState`、`GetPose` 等本地未证实的接口。
- “暂停/改变天气/截图”：先查当前版本真实支持的命令或接口定义。手册未覆盖不代表不存在，但不能用猜测的 endpoint 发送写请求。

完成时给出简短结果，例如“ego：FL/FR/RL/RR 读回均为 0.9，已保持新设置”；仅预览、受权限阻塞或没有效果观测时明确说出该状态。
