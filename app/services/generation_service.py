import re

from app.schemas.brief import ThemeBrief
from app.schemas.test_config import (
    Dimension,
    DimensionGroup,
    OptionConfig,
    PageConfig,
    Question,
    ResultConfig,
    RuleConfig,
    ScoringConfig,
    TestConfig,
    TestMeta,
)


LEVELS = ["L", "M", "H"]


class GenerationService:
    """Deterministic MVP draft generator.

    The product calls this "AI generation" in the UI, but the MVP keeps a local
    generator so the app is runnable without an API key. The service boundary is
    intentionally the same one a real model provider would use later.
    """

    def generate_from_brief(self, brief: ThemeBrief) -> TestConfig:
        test_id = self._slugify(brief.topic)
        groups = self._groups()
        dimensions = self._dimensions(brief, groups)
        questions = self._questions(brief, dimensions)
        results = self._results(brief, dimensions)
        rules: list[RuleConfig] = []

        if brief.allow_hidden_results:
            questions.append(
                Question(
                    id="q_gate_chaos",
                    text=f"如果把「{brief.topic}」变成一种深夜冲动，你最像哪一种？",
                    dimension_id=None,
                    is_scored=False,
                    is_gate=True,
                    options=[
                        OptionConfig(id="a", text="安静围观，明天再说"),
                        OptionConfig(id="b", text="突然上头，直接发疯"),
                        OptionConfig(id="c", text="看大家先疯，我负责截图"),
                    ],
                )
            )
            results.append(
                ResultConfig(
                    id="CHAOS",
                    code="CHAOS",
                    name="彩蛋失控者",
                    kind="hidden",
                    priority=1000,
                    headline="你不是在参与测试，你是在给系统施压。",
                    description=f"在「{brief.topic}」这件事上，你的精神状态已经绕过常规评分，直接抵达隐藏出口。你不一定最强，但你很难被普通模板解释。",
                    share_text="我测出了隐藏人格 CHAOS，这合理吗？",
                )
            )
            rules.append(
                RuleConfig(
                    id="chaos_gate",
                    question_id="q_gate_chaos",
                    option_id="b",
                    result_id="CHAOS",
                    priority=1000,
                )
            )

        results.append(
            ResultConfig(
                id="MIXED",
                code="MIX",
                name="混合型路过人",
                kind="fallback",
                priority=-1,
                headline="你的答案把标准人格库绕晕了。",
                description=f"你在「{brief.topic}」里的表现不太像任何标准模板。也许你不是没有人格，而是每个场景都临时加载一套插件。",
                share_text="我测出了混合型，系统说我很难分类。",
            )
        )

        return TestConfig(
            meta=TestMeta(
                test_id=test_id,
                name=f"{brief.topic} XBTI",
                subtitle=f"测测你在「{brief.topic}」里是哪种精神体",
                description=f"一个面向{brief.audience}的趣味测试，语气方向是{brief.tone}。",
            ),
            dimension_groups=groups,
            dimensions=dimensions,
            questions=questions,
            results=results,
            rules=rules,
            scoring=ScoringConfig(fallback_result_id="MIXED", shuffle_questions=True),
            page=PageConfig(accent_color="#2f9e44"),
        )

    def _groups(self) -> list[DimensionGroup]:
        return [
            DimensionGroup(id="self", name="自我模型", description="你如何理解自己的状态。"),
            DimensionGroup(id="relation", name="关系模型", description="你如何靠近或远离别人。"),
            DimensionGroup(id="world", name="世界模型", description="你如何判断外部环境。"),
            DimensionGroup(id="action", name="行动模型", description="你如何推进事情。"),
            DimensionGroup(id="expression", name="表达模型", description="你如何被别人看见。"),
        ]

    def _dimensions(self, brief: ThemeBrief, groups: list[DimensionGroup]) -> list[Dimension]:
        names = [
            ("自我启动", "更慢热回血", "状态看天气", "自己给自己点火"),
            ("边界清晰", "容易被带走", "看对象调节", "边界很硬"),
            ("目标浓度", "先舒服再说", "想冲也想躺", "目标感很强"),
            ("情绪投入", "点到为止", "半开半关", "很容易认真"),
            ("安全感", "警报灵敏", "信任和怀疑拉扯", "基本稳定"),
            ("亲密需求", "需要贴近", "亲近和空间都要", "更爱独立"),
            ("乐观滤镜", "先怀疑", "先观察", "愿意相信好事"),
            ("规则感", "能绕则绕", "该守才守", "流程让人安心"),
            ("意义感", "很多事都随缘", "偶尔清醒偶尔摆", "需要一个方向"),
            ("推进欲", "别翻车就行", "看情况推进", "不落地会难受"),
            ("决策速度", "脑内开会", "犹豫但能定", "拍板很快"),
            ("执行节奏", "死线触发", "间歇稳定", "持续推进"),
            ("社交主动", "慢热观望", "有人来就接", "主动开场"),
            ("人际距离", "容易融合", "保留一点缝", "靠太近会退"),
            ("表达真实", "直给", "看气氛", "会切换面具"),
            ("审美偏好", "务实耐看", "都能欣赏", "风格要鲜明"),
            ("风险胃口", "稳住别浪", "小试一下", "越刺激越醒"),
            ("幽默方式", "冷静吐槽", "适度玩梗", "自带气氛组"),
            ("资源分配", "省着点用", "按需投入", "该花就花"),
            ("复盘强度", "过去就算", "偶尔回看", "必须总结"),
            ("好奇心", "熟悉区安全", "新旧都可", "喜欢开新地图"),
            ("掌控感", "随它去吧", "能控则控", "最好我来"),
            ("共情浓度", "先讲事实", "情理都看", "很能感受别人"),
            ("反叛指数", "别惹麻烦", "偶尔不服", "规则先质疑"),
        ]
        dimensions: list[Dimension] = []
        for index in range(brief.dimension_count):
            name, low, mid, high = names[index % len(names)]
            group = groups[index % len(groups)]
            dimensions.append(
                Dimension(
                    id=f"D{index + 1}",
                    group_id=group.id,
                    name=name,
                    description=f"在「{brief.topic}」主题下衡量{name}。",
                    low_label=low,
                    mid_label=mid,
                    high_label=high,
                )
            )
        return dimensions

    def _questions(self, brief: ThemeBrief, dimensions: list[Dimension]) -> list[Question]:
        questions: list[Question] = []
        for index in range(brief.question_count):
            dimension = dimensions[index % len(dimensions)]
            questions.append(
                Question(
                    id=f"q{index + 1}",
                    text=f"关于「{brief.topic}」的第 {index + 1} 个场景，你更接近哪种反应？",
                    dimension_id=dimension.id,
                    options=[
                        OptionConfig(id="a", text=f"{dimension.low_label}，先别把我推上台。", score=1),
                        OptionConfig(id="b", text=f"{dimension.mid_label}，我看情况切换。", score=2),
                        OptionConfig(id="c", text=f"{dimension.high_label}，这事我可以接。", score=3),
                    ],
                )
            )
        return questions

    def _results(self, brief: ThemeBrief, dimensions: list[Dimension]) -> list[ResultConfig]:
        result_names = [
            ("CTRL", "拿捏调度员"),
            ("GOGO", "冲锋执行者"),
            ("MUM", "温柔补给站"),
            ("MONK", "边界修行者"),
            ("JOKE", "气氛承包商"),
            ("THINK", "深度复盘人"),
            ("LOVE", "热烈投入派"),
            ("SOLO", "独行观察员"),
            ("BOSS", "方向盘本人"),
            ("ZZZ", "低电量潜伏者"),
            ("FAKE", "场景切换师"),
            ("WILD", "野生反叛者"),
        ]
        results: list[ResultConfig] = []
        for index in range(brief.result_count):
            code, name = result_names[index % len(result_names)]
            code = f"{code}{index // len(result_names) + 1}" if index >= len(result_names) else code
            template = [LEVELS[(index + dim_index * 2) % 3] for dim_index in range(len(dimensions))]
            results.append(
                ResultConfig(
                    id=code,
                    code=code,
                    name=name,
                    kind="standard",
                    template=template,
                    priority=brief.result_count - index,
                    headline=f"你在「{brief.topic}」里像一个{name}。",
                    description=(
                        f"{name}不是一个冷冰冰的标签，而是一种在「{brief.topic}」场景里反复出现的姿态。"
                        f"你有自己的节奏，也有一点说不清的坚持。别人以为你只是随便选选，"
                        f"但系统已经看见了你那些微妙的小动作。"
                    ),
                    share_text=f"我测出了{name}，有点准又有点离谱。",
                )
            )
        return results

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return slug or "xbti-test"
