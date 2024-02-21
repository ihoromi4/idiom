# V 0.3.0
- Use web-compatible GUI library
- Move language model to separate service
- Use [bark](https://huggingface.co/suno/bark) TTA model instead of `bark-small`

# V 0.2.0
- Use `SQLite` database with `SQLAlchemy` ORM
- Save generated audio to file system using `?` compression format
- Save exercise results to database
- Compute complexity score of exercises

# V 0.1.0
- Use [bark-small](https://huggingface.co/suno/bark-small) TTA model from `huggingface` for audio generation
- Generate audio in separate process using `multiprocessing` library
- Keep cache of N=5 exercises with generated audio
- Use `PySide6` for GUI
- Use predefined list of English dictation exercises
