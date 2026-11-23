# ASSETS — OUR SCHOOL, OUR MEMORIES

Every number below was read from the real files by `tools/inspect-assets.py`
(raw output: `tools/inspect-report.json`). Content descriptions come from looking at
each file. Originals are copied untouched into `originals/`; all processed output
goes to `build/` and `public/assets/`.

> 实际上传文件是 **20 个**，不是规格书里写的 16 个：8 个 GIF、2 个 PNG、9 个 JPG、1 个规格文档 (txt)。

## 1. 角色 GIF（8 个，全部已核对内容）

| 文件 | 内容（已看过帧） | 尺寸 | 帧数 | 帧时间 | 背景 | 用途 / 处理 |
|---|---|---|---|---|---|---|
| 1000088014.gif | 男 正面待机（含眨眼、动作线） | 439×389 | 8 | 300 ms | 浅蓝 (170,220,253) | `male front_idle`，已清除动作线与影子 |
| 1000088016.gif | 男 正面行走 | 438×390 | 9 | 120 ms | 浅蓝 | `male front_walk` |
| 1000088019.gif | 男 背面行走 | 436×388 | 9 | 120 ms | 浅蓝 | `male back_walk` |
| 1000088040.gif | 男 向左行走 | 439×390 | 9 | 120 ms | 浅蓝 | `male left_walk` |
| 1000088015.gif | 女 正面待机（含眨眼、动作线） | 439×390 | 9 | 220 ms | 白 | `female front_idle` |
| 1000088017.gif | 女 正面行走 | 436×388 | 9 | 120 ms | 白 | `female front_walk` |
| 1000088020.gif | 女 背面行走 | 435×386 | 9 | 140 ms | 白 | `female back_walk` |
| 1000088041.gif | 女 向左行走 | 435×386 | 9 | 120 ms | 白 | `female left_walk` |

所有 GIF 均**无透明通道**（背景是实心色），循环次数 0（无限）。

## 2. 角色静态图（6 个）

| 文件 | 内容 | 尺寸 | 背景 | 用途 |
|---|---|---|---|---|
| 1000087104.jpg | 男 正面站立（大图） | 1200×1122 | 浅蓝 | 角色选择界面大图参考 |
| 1000087100.jpg | 女 正面站立（大图） | 1200×1176 | 近白 | 角色选择界面大图参考 |
| 1000088018.png | 男 背面行走（大图） | 1330×1182 | 浅蓝 | 背面参考，与 019 对照 |
| 1000088047.jpg | 男 背面站立（大图） | 1200×1047 | 浅蓝 | 背面待机参考 |
| 1000088049.jpg | 女 **坐姿**正面 | 1200×1152 | 白 | `female sit_front`（已清底） |
| 1000088051.jpg | 女 **坐姿**背面 | 1200×1147 | 白 | `female sit_back`（已清底） |

**没有男生坐姿素材。** 男生坐姿由行走帧"上半身 + 折叠小腿"程序生成，标记为 `generated`。

## 3. 场景 / 界面参考（5 个）

| 文件 | 内容 | 尺寸 | 用途 |
|---|---|---|---|
| 1000086903.png | 学校正门像素风立面：蓝色招牌 "SJK (C) JENJAROM / 仁嘉隆国民型华文学校"、铁闸门、外墙校名牌、楼梯 | 1672×941 | 主菜单背景参考。注意：左侧蓝色告示牌上的中文是乱码，不可当作真实文字使用 |
| 1000087985.jpg | 礼堂：**从观众席看向舞台**（大屏幕、讲台、两侧高处小屏幕、侧墙二楼走廊栏杆、红色通道、黄/红座位） | 1526×688 | 礼堂一楼布局依据 |
| 1000087982.jpg | 礼堂：**从舞台看向后方**（后方二楼栏杆上的绿屏、后方中央出口、出口右侧玻璃控制室、两根黄色柱子、侧墙门） | 1376×768 | 后方出口 / 控制室 / 后方屏幕依据 |
| 1000088052.jpg | 从**玻璃控制室内部**看向舞台（调音台、两台显示器、机柜） | 1526×688 | 控制区域内部布局依据 |
| 1000088013.jpg | AUDITORIUMC "Presentation Control Center" 界面截图：PPT Player / PPT Games / Screen Sync / My Files + 右侧三个屏幕 | 1200×675 | 电脑一界面视觉参考（蓝白）。截图中有乱码文字，需重写 |

## 4. 规格文档

| 文件 | 说明 |
|---|---|
| attachment.txt | 规格书 v3.0（27,575 bytes） |

## 5. 照片能确认 / 不能确认的内容

**能确认（有照片依据）**
- 舞台在前方；舞台正中有大绿屏与讲台；舞台左右墙高处各有一块绿屏。
- 后方二楼栏杆正中有一块绿屏（后方屏幕）→ 四个屏：主舞台、左、右、后方。
- 中央红色通道；左右各一大片黄色座位；红色座位在黄色座位前方（靠近舞台）和后方两侧。
- 后方中央出口；出口**右侧**（从舞台看向后方）为玻璃控制室，内有调音台、两台显示器、机柜。
- 两根黄色柱子在出口两侧。
- 左右侧墙下方有多扇深色双开门，上方有二楼走廊 + 红色绸带栏杆。

**不能确认（一律标 `NEEDS_REFERENCE`，用可替换占位）**
- 二楼走廊内部的真实布局、楼梯内部位置与形状。
- 舞台两侧通往二楼的门的确切位置（照片里能看到侧墙上有门，但没有一张照片显示门后是什么）。
- Building 1/2/3 的任何结构（**没有任何照片**，只有 Building 4 礼堂内部与正门立面）。
- 校园道路、操场、花圃的位置关系（没有航拍或总平面照片）。

## 6. 处理流程（可复现）

```
python3 -I tools/inspect-assets.py originals     # 元数据
python3 -I tools/clean_frames.py                 # 去背景/影子/动作线 → build/frames/
python3 -I tools/build_sprites.py                # 对齐/缩放/衍生动作/打包 → public/assets/characters/
```

输出：`characters_male|female.png/.json`（Phaser JSON-hash 图集，每帧 128×120，脚底锚点 y=114/120，躯干中心 x=64）与 `animations.json`（每个动画都带 `source` 来源字段）。

## 7. 动画来源说明（诚实标注）

| 来源 | 含义 | 哪些动画 |
|---|---|---|
| `gif` | 直接取自上传 GIF | front_idle, front_walk, back_walk, left_walk（男女各自） |
| `gif-still` | 取 GIF 一帧做静止姿势 | back_idle, left_idle |
| `mirrored` | 左向动画水平镜像 | right_walk, right_idle（背包仍在身后，几何上正确） |
| `art` | 上传的坐姿图 | female sit_front, sit_back |
| `generated` | 脚本程序生成，**不是原始美术** | 四个方向的 run、四个方向的 interact（原地跳跃反馈）、male sit_*、sit_left / sit_right |

> run 是 6 帧重新挑选 + 更大弹跳 + 侧向前倾（错切），不是把走路加速。
> interact 只有轻微跳跃/挤压，因为素材里没有手臂动作。
