`/tasks`

Methods:

`post`:

Description: Create a video indexing task

Parameters:

```json
{
  "video_file": TODO
}
```

Responses:

`201` - Video indexing task has been successfully created

```json
{
  "id": string,
  "video_id": string
}
```

`get`:

Description: Return a list of tasks

Responses:

`200` - OK

```json
{
  "data": [
    {
      "id": string,
      "created_at": string,
      "updated_at": string,
      "total_duration": integer,
      "status": string,
      "metadata": {
        "duration": integer,
        "filename": string,
        "height": integer,
        "width": integer
      }
    }
  ]
}
```

`/tasks/{id}`

Methods:

`get`:

Description: Return a specific task

Responses:

`200` - OK

```json
{
  "id": string,
  "created_at": string,
  "status": string,
  "updated_at": string,
  "video_id": string,
  "metadata": {
    "duration": integer,
    "filename": string,
    "height": integer,
    "width": integer
  }
}
```

`delete`:

Description: Delete a specific task

Parameters:

```json
{
  "id": integer
}
```

Responses:

`200` - OK

`400` - Error

`/search`

Methods

`post`:

Parameters:

```json
{
  "query_text": string,
  "page_limit": integer (optional),
  "min_similarity": float (optional)
}
```

Response:

`200`

```json
{
  "data": [
    {
      "score": float,
      "start_offset": float,
      "end_offset": float,
      "video_id": string,
      "thumbnail_url": string,
    }
  ]
}
```

`get`
