import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
import traceback
import subprocess
from utils.save_vids import *
from utils.logger import get_logger
from main import get_inventory_informations, load_yaml

logger = get_logger("api_server")
config = load_yaml("configs/config.yaml")

app = FastAPI(
    title="Inventory Processing API",
    description="API for warehouse inventory video processing",
    version="1.0.0"
)

class VideoInput(BaseModel):
    video_input: Union[str, List[str]]
    output_path: str = "outputs"

@app.post("/process-videos/")
async def process_videos_endpoint(data: VideoInput):
    """
    Endpoint to receive video path(s) and start the processing.
    - **video_input**: Path to a video (str) or list of paths (list[str]).
    - **output_path**: Directory to save results.
    """
    try:
        logger.info(f"Received processing request for: {data.video_input}")

        dict_total = get_inventory_informations(
            video_input=data.video_input,
            output_path=data.output_path,
            config=config
        )
        
        if not dict_total:
            logger.warning("Processing completed but no data returned.")
            return {"message": "Processing finished but no data found."}


        logger.info("Processing successful. Returning results.")

        return dict_total

    except FileNotFoundError as e:
        tb = traceback.format_exc()
        logger.error(f"File not found: {e}")
        logger.error(tb)
        raise HTTPException(
            status_code=404,
            detail={
                "error": str(e),
                "traceback": tb.splitlines()
            }
        )

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error occurred: {e}")
        logger.error(tb)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": tb.splitlines()
            }
        )
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
