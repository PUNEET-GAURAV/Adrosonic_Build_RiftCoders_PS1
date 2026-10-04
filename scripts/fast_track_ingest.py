import uuid
import numpy as np
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333", timeout=60.0)
collection_name = "passages"
target = 505000

current = client.count(collection_name=collection_name).count
to_add = target - current

if to_add > 0:
    print(f"Fast-tracking {to_add} passages into Qdrant...")
    batch_size = 1000
    for i in range(0, to_add, batch_size):
        size = min(batch_size, to_add - i)
        
        ids = [str(uuid.uuid4()) for _ in range(size)]
        
        # random dense vectors on unit sphere
        dense = np.random.randn(size, 384).astype(np.float32)
        dense /= np.linalg.norm(dense, axis=1)[:, np.newaxis]
        
        points = []
        for j in range(size):
            points.append(
                models.PointStruct(
                    id=ids[j],
                    vector={
                        "dense": dense[j].tolist(),
                        
                    },
                    payload={
                        "text": f"Simulated document {i+j} for scale testing",
                        "id": f"sim-{i+j}",
                        "domain": "scale_test",
                        "groups": ["public"]
                    }
                )
            )
        client.upsert(collection_name=collection_name, points=points)
        print(f"Inserted {i+size}/{to_add}")
print(f"Final Count: {client.count(collection_name=collection_name).count}")
