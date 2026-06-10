# ontology

## Публикация в WordPress

Этот репозиторий является источником Markdown-документов для публичного архива
`source_document` на `deconreality.com`. Настройки выборки находятся в
`.content-sync.yml`, запуск — в GitHub Actions workflow
`sync-to-wordpress.yml`.

По умолчанию ручной запуск выполняется в режиме `dry_run`. Для публикации нужно
снять этот флаг и предварительно добавить в GitHub Secrets:

```text
WP_URL
WP_USERNAME
WP_APP_PASSWORD
```

Поле `path` позволяет сначала проверить или опубликовать один файл, например
`Introduction.md`. Если оно пустое, обрабатывается вся настроенная выборка.

Общий синхронизатор и WordPress-плагин хранятся в репозитории
`IBobko/deconreality`.

- [Введение](Introduction.md)
- [Что такое реальность: внутренний и внешний слои](RealityInternalAndExternal.md)
- [Что такое различение](Distinction/Distinction.md)
- [Фазы различения](PhasesOfDistinction.md)
- [Что такое поле переживания](FieldOfExperience.md)
- [Что такое событие](Event.md)
- [Режимы обработки](TwoModesOfThinking.md)
- [Страх как сжатие пространства различений](Fear.md)
- [Эмоция как форма: слабый вариант для навигации](Emotion.md)
- [О важности вопроса «почему»](ImportanceOfWhyQuestion.md)
- [Сознание как способность различать](ConsciousnessAsDistinctionCapacity.md)
- [Абсолютное сознание, различение и время](AbsoluteConsciousnessAndTime.md)
- [Динамика формы и смысла](FormAndMeaningDynamics.md)
- [Линейность](Linearity.md)
- [Смысловое поле](SemanticField.md)
- [Система как форма](System/SystemAsForm.md)
- [Любая система имеет «идеального человека»](IdealSubjectInAnySystem.md)
- [Методологический натурализм и прозрачность рамки](MethodologicalNaturalismAndFrameworkTransparency.md)
- [Эпистемология: как возможно знание](Epistemology.md)
- [Две философские линии: каталог сущностей и генезис опыта](PhilosophyCatalogVsExperience.md)
- [Критическое мышление](CriticalThinking.md)
- [Сглаживание](smoothing.md)
- [Бесконечность, замкнутость и идеологичность теорий](Infinity.md)
- [Риторические контейнеры: рабочий документ](RhetoricalContainers.md)
- [Кто такой либерал](WhoIsLiberal.md)

- [Что такое рациональность](Rationality.md)

- [Внешний и внутренний источник истины: два режима зрелости](ExternalVsInternalSourceOfTruth.md)
- [Инструкция: что делать, если git «сломался» после rebase](GitRecoveryGuide.md)
- [Экстраполяция как инструмент проверки утверждений](Extrapolation.md)
- [Что такое аксиоматика](Axiomatics.md)
- [Что такое аксиома](Axiom.md)
- [Что такое формальная система](System/FormalSystem.md)
- [Логика как частный случай введённых правил](LogicAsFrameworkBoundTool.md)
- [Что такое парадокс](Paradox.md)
- [Фиксация логики программирования субъекта в сущностях](Subject/SubjectnessInEntities.md)
- [«Иллюзия» как риторическая операция](IllusionAsRhetoricalOperation.md)
- [Сарказм: конфликт формы и смысла](Sarcasm.md)
- [Мат как носитель интенсивности смысла](Profanity.md)
- [Обман как обрезание смысла ради поддержания формы](Deception.md)

- [Фиксация комментария apgapg67 к посту на Habr](Habr_apgapg67_post_944470_comment.md)

## Мета-раздел

- [Восприятие как сборка: конспект](Perception.md)
- [Что такое различение](Distinction/Distinction.md)
- [Конспект: описание, восприятие и различение](Description.md)
