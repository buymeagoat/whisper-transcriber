```
 [Frontend]
     |
     | HTTP / WebSocket
     v
 [API] <-----> [Worker]
     |              |
     | REST/DB      |
     v              v
 [Database]    [Storage]
     ^              |
     | logs         |
     +----> [System Log]

Dashed boxes represent optional components when JOB_QUEUE_BACKEND=thread or STORAGE_BACKEND=local.
```
