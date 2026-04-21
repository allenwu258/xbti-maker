from app.schemas.scoring import CandidateScore, ScoreResult
from app.schemas.test_config import ResultConfig, TestConfig


LEVEL_VALUE = {"L": 0, "M": 1, "H": 2}
VALUE_LEVEL = {0: "L", 1: "M", 2: "H"}


class ScoringService:
    def score(self, config: TestConfig, answers: dict[str, str]) -> ScoreResult:
        result_by_id = {result.id: result for result in config.results}
        triggered = self._triggered_rules(config, answers)
        dimension_scores = self._dimension_scores(config, answers)
        dimension_levels = self._dimension_levels(config, dimension_scores)
        user_vector = [dimension_levels[dimension.id] for dimension in config.dimensions]
        candidates = self._rank_candidates(config, user_vector)

        if triggered:
            result_id = triggered[0]
            return ScoreResult(
                result_id=result_id,
                similarity=100,
                dimension_scores=dimension_scores,
                dimension_levels=dimension_levels,
                user_vector=user_vector,
                candidates=candidates,
                triggered_rules=[result_id],
            )

        winner = candidates[0] if candidates else None
        if not winner:
            fallback_id = config.scoring.fallback_result_id
            return ScoreResult(
                result_id=fallback_id,
                similarity=0,
                dimension_scores=dimension_scores,
                dimension_levels=dimension_levels,
                user_vector=user_vector,
                candidates=[],
                triggered_rules=[],
            )

        result_id = winner.result_id
        similarity = winner.similarity
        if similarity < config.scoring.min_similarity and config.scoring.fallback_result_id in result_by_id:
            result_id = config.scoring.fallback_result_id

        return ScoreResult(
            result_id=result_id,
            similarity=similarity,
            dimension_scores=dimension_scores,
            dimension_levels=dimension_levels,
            user_vector=user_vector,
            candidates=candidates,
            triggered_rules=[],
        )

    def _triggered_rules(self, config: TestConfig, answers: dict[str, str]) -> list[str]:
        valid_results = {result.id for result in config.results}
        triggered: list[tuple[int, str]] = []
        for rule in config.rules:
            if rule.result_id not in valid_results:
                continue
            if answers.get(rule.question_id) == rule.option_id:
                triggered.append((rule.priority, rule.result_id))
        triggered.sort(key=lambda item: item[0], reverse=True)
        return [result_id for _, result_id in triggered]

    def _dimension_scores(self, config: TestConfig, answers: dict[str, str]) -> dict[str, float]:
        scores = {dimension.id: 0.0 for dimension in config.dimensions}
        question_by_id = {question.id: question for question in config.questions}

        for question_id, option_id in answers.items():
            question = question_by_id.get(question_id)
            if not question or not question.is_scored or not question.dimension_id:
                continue
            option = next((item for item in question.options if item.id == option_id), None)
            if option and option.score is not None:
                scores[question.dimension_id] = scores.get(question.dimension_id, 0.0) + option.score

        return scores

    def _dimension_levels(self, config: TestConfig, scores: dict[str, float]) -> dict[str, str]:
        levels: dict[str, str] = {}
        questions_by_dimension = {
            dimension.id: [
                question
                for question in config.questions
                if question.is_scored and question.dimension_id == dimension.id
            ]
            for dimension in config.dimensions
        }

        for dimension in config.dimensions:
            questions = questions_by_dimension[dimension.id]
            min_score = 0.0
            max_score = 0.0
            for question in questions:
                scored_options = [option.score for option in question.options if option.score is not None]
                if not scored_options:
                    continue
                min_score += min(scored_options)
                max_score += max(scored_options)

            raw_score = scores.get(dimension.id, 0.0)
            if max_score <= min_score:
                normalized = 0.5
            else:
                normalized = (raw_score - min_score) / (max_score - min_score)
                normalized = max(0.0, min(1.0, normalized))

            if normalized <= config.scoring.low_max:
                levels[dimension.id] = "L"
            elif normalized <= config.scoring.mid_max:
                levels[dimension.id] = "M"
            else:
                levels[dimension.id] = "H"

        return levels

    def _rank_candidates(self, config: TestConfig, user_vector: list[str]) -> list[CandidateScore]:
        standard_results = [result for result in config.results if result.kind == "standard"]
        max_distance = sum(dimension.weight * 2 for dimension in config.dimensions) or 1
        candidates: list[CandidateScore] = []

        for result in standard_results:
            if len(result.template) != len(config.dimensions):
                continue
            distance = self._distance(config, user_vector, result)
            exact_matches = sum(1 for left, right in zip(user_vector, result.template) if left == right)
            similarity = round((1 - distance / max_distance) * 100)
            candidates.append(
                CandidateScore(
                    result_id=result.id,
                    code=result.code,
                    name=result.name,
                    distance=distance,
                    exact_matches=exact_matches,
                    similarity=max(0, min(100, similarity)),
                    priority=result.priority,
                )
            )

        candidates.sort(
            key=lambda item: (
                item.distance,
                -item.exact_matches,
                -item.priority,
                item.result_id,
            )
        )
        return candidates

    def _distance(self, config: TestConfig, user_vector: list[str], result: ResultConfig) -> float:
        total = 0.0
        for index, dimension in enumerate(config.dimensions):
            total += dimension.weight * abs(
                LEVEL_VALUE[user_vector[index]] - LEVEL_VALUE[result.template[index]]
            )
        return total
