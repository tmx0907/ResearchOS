# 📊 비교 테이블 (Dataview)

```dataview
TABLE year AS "Year", method AS "Method", measurement AS "Tools", sample_size AS "N", effect_size AS "ES", reading_priority AS "P", relevance_score AS "Rel"
FROM "02_cards_basic"
SORT relevance_score DESC
```

## 🔴 Must-Read

```dataview
TABLE year AS "Year", journal AS "Journal", method AS "Method"
FROM "02_cards_basic"
WHERE reading_priority = "must-read"
SORT relevance_score DESC
```
