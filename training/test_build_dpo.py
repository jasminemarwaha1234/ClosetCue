import json

from backend.services import supabase
from training.build_dpo import main

PROMPT = [{"role": "system", "content": "You are a personal stylist."}, {"role": "user", "content": "Style profile: ..."}]
CHOSEN = '{"outfits":[{"items":["top_001","bottom_002"],"reason":"Wear the black top with the olive bottom."}]}'
REJECTED = '{"outfits":[{"items":["top_001","bottom_001"],"reason":"Start from the black top."}]}'


def test_cli_writes_preference_rows_for_one_model(tmp_path, monkeypatch, capsys):
    async def rows():
        return [
            {"id": 1, "user_id": "u1", "prompt": PROMPT, "chosen": CHOSEN, "rejected": REJECTED,
             "rejected_model": "our-llama", "request": {}, "created_at": "2026-10-18T10:00:00Z"},
            {"id": 2, "user_id": "u1", "prompt": PROMPT, "chosen": CHOSEN, "rejected": REJECTED,
             "rejected_model": "base-llama", "request": {}, "created_at": "2026-10-18T10:01:00Z"},
        ]

    monkeypatch.setattr(supabase, "list_preferences", rows)
    out = tmp_path / "dpo.jsonl"
    monkeypatch.setattr("sys.argv", ["build_dpo", "--out", str(out)])
    main()
    assert [json.loads(line) for line in out.read_text().splitlines()] == [
        {"prompt": PROMPT, "chosen": [{"role": "assistant", "content": CHOSEN}],
         "rejected": [{"role": "assistant", "content": REJECTED}]},
    ]
    assert capsys.readouterr().out == f"wrote 1 of 2 preference rows to {out}; 1 turned down another model\n"
