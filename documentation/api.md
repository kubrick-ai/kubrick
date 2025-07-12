# APIs

## Create a video indexing task
### Request
Description: Creates a video indexing Task object.

Endpoint: `/tasks`

Methods: `POST`

Parameters:

```json
{
  "video_file": TODO
}
```

### Successful Response

`201` - Video indexing task has been successfully created

```json
{
  "id": uuid string,
  "status": "processing",
  "video_url": "url_to_video_thats_hosted_somewhere"
}
```

**Note**: There are no error response, see GET "/tasks/task_id" endpoint

## Return a List of tasks
Description: Returns all the Task objects stored in Task_Stored object

Endpoint: `/tasks`

Methods: `GET`

Parameters [OPTIONAL]:
```bash
/tasks?page=1
```
**Note**: Default is 1

### Successful Response

`200` - OK

**To be implemented:**
```json
{
  "tasks": [
    {
      ~"id": string,
      "created_at": string,
      "updated_at": string,
      "total_duration": integer,
      "status": string,
      "metadata": {
        "duration": integer,
        "filename": string,
        "height": integer,
        "width": integer
    },
  ]
}
```

**How it currently works**
```json
{
    "tasks": [
        {
        "completed_at": string date,
        "created_at": string date,
        "status": "processing" | "ready" | "failed",
        "task_id": uuid string,
        "video_url": string url,
        },
    ]
}
```
## Return a specific task
### Request
Description: Use this endpoint to query for status of task

Endpoint: `/tasks/{id}`

Methods: `GET`

Parameters:


### Successful Response

`200` - OK

**To be implemented:**
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
**How it currently works**
```json
{
    "tasks": [
        {
        "error": null | "Failed to download video. HTTP 403",
        "status": "processing" | "ready" | "failed",
        "task_id": uuid string,
        }
    ]
}
```

## Delete a task
Description: Delete a specific task

Endpoint: `/delete`

Methods: `DELETE`

Parameters:

```json
{
  "id": integer
}
```

### Successful Response

`200` - OK

### Error Response

`400` - Error

## Query Search
Description: Semantic query

Endpoint: `/search`

Methods: `POST`

Parameters:

```json
{
  "query_text": string,
  "query_media_type": "image" | null,
  "query_media_file": TODO,
  "page_limit": integer
}
```

Response:

`200`

```json
{
  "data": [
    {
      "score": float,
      "start": float,
      "end": float,
      "video_id": string,
      "thumbnail_url": string,
    }
  ]
}
```

`get`
