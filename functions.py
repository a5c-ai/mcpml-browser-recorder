import logging
import yaml
from pathlib import Path
from playwright.sync_api import sync_playwright, Playwright, Page, BrowserContext, Error
import time

logger = logging.getLogger(__name__)

def execute_script(page: Page, context: BrowserContext, script_steps: list):
    """Executes the parsed script steps."""
    for i, step in enumerate(script_steps):
        action = step.get("action")
        params = step.get("params", {})
        logger.info(f"Executing step {i+1}: {action} with params {params}")

        try:
            if action == "goto":
                page.goto(params["url"])
            elif action == "wait": # Simple wait for demonstration
                time.sleep(params.get("seconds", 1))
            elif action == "screenshot":
                screenshot_path = params.get("path", f"step_{i+1}_screenshot.png")
                page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            elif action == "click":
                page.click(params["selector"])
            elif action == "fill":
                page.fill(params["selector"], params["value"])
            # Add more actions as needed (e.g., type, select_option, check, etc.)
            else:
                logger.warning(f"Unknown action: {action}")
        except Error as e:
            logger.error(f"Playwright Error during step {i+1} ({action}): {e}")
            raise # Re-raise to stop execution on error
        except KeyError as e:
            logger.error(f"Missing required parameter '{e}' for action '{action}' in step {i+1}")
            raise # Re-raise to stop execution on error

def record_session(script_path: str, output_path: str):
    """Records a browser session based on a script.

Script format (or absolute yaml file path to the script):
- action: goto
  params:
    url: "https://intuitive-website2.azurewebsites.net/"
- action: wait
  params:
    seconds: 2
- action: screenshot
  params:
    path: "session_output/intuitive_home.png" # Note: This path is relative to the page context, not output_path
- action: fill
  params:
    selector: "input[id='name']" # Selector for Google search box
    value: "Playwright browser automation"
- action: wait
  params:
    seconds: 1
- action: fill
  params:
    selector: "input[id='email']" # Selector for Google search box
    value: "playwright@intuitive.com"
- action: wait
  params:
    seconds: 1
- action: fill
  params:
    selector: "input[id='company']" # Selector for Google search box
    value: "Intuitive"
- action: wait
  params:
    seconds: 1        
- action: fill
  params:
    selector: "textarea[id='message']" # Selector for Google search box
    value: "Playwright browser automation"
- action: wait
  params:
    seconds: 1
- action: click
  params:
    selector: "button[type='submit']" # Selector for Google Search button (might vary)
- action: wait
  params:
    seconds: 3 # Wait for search results
- action: screenshot
  params:
    path: "session_output/intuitive_contact.png"    


    Args:
        script: The script content (format TBD).
        output_path: The directory to save output files.

    Returns:
        A dictionary containing the status and paths to the generated files.
    """
    logger.info(f"Starting session recording...")
    if(script_path.endswith(".yaml")):
        script = Path(script_path).read_text()
    else:
        script = script_path
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_formats: list[str] = ["video", "log", "screenshot"]
    result = {
        "status": "failed", # Default to failed
        "message": "",
        "outputs": {}
    }

    try:
        script_data = yaml.safe_load(script)
        if not isinstance(script_data, list):
            raise ValueError("Script must be a list of steps.")
    except yaml.YAMLError as e:
        result["message"] = f"Failed to parse script YAML: {e}"
        logger.error(result["message"])
        return result
    except ValueError as e:
        result["message"] = str(e)
        logger.error(result["message"])
        return result

    logger.debug(f"Parsed Script: {script_data}")
    logger.debug(f"Output Path: {output_path}")
    logger.debug(f"Output Formats: {output_formats}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) # Or False for debugging
            context_args = {}
            video_path = None

            if "video" in output_formats:
                video_path = output_dir / "session.mp4"
                context_args["record_video_dir"] = str(output_dir)
                context_args["record_video_size"] = {"width": 1280, "height": 720}
                logger.info(f"Video recording enabled, saving to {output_dir}")

            context = browser.new_context(**context_args)
            page = context.new_page()

            # Basic log capture (console messages)
            log_path = None
            log_lines = []
            if "log" in output_formats:
                log_path = output_dir / "session.log"
                page.on("console", lambda msg: log_lines.append(f"[{msg.type}] {msg.text}"))
                logger.info(f"Console logging enabled, saving to {log_path}")

            try:
                execute_script(page, context, script_data)
                result["status"] = "success"
                result["message"] = "Session recording completed successfully."

                if "screenshot" in output_formats:
                    screenshot_path = output_dir / "final_screenshot.png"
                    page.screenshot(path=screenshot_path)
                    result["outputs"]["screenshot"] = str(screenshot_path)
                    logger.info(f"Final screenshot saved to {screenshot_path}")

            except Exception as e:
                 result["message"] = f"Error during script execution: {e}"
                 logger.error(result["message"])
                 # Capture screenshot on error if possible
                 try:
                     error_screenshot_path = output_dir / "error_screenshot.png"
                     page.screenshot(path=error_screenshot_path)
                     result["outputs"]["error_screenshot"] = str(error_screenshot_path)
                     logger.info(f"Error screenshot saved to {error_screenshot_path}")
                 except Exception as screenshot_err:
                     logger.error(f"Could not take error screenshot: {screenshot_err}")

            finally:
                 # Save logs if enabled
                 if log_path:
                    try:
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(log_lines))
                        result["outputs"]["log"] = str(log_path)
                        logger.info(f"Logs saved to {log_path}")
                    except IOError as e:
                        logger.error(f"Failed to write log file: {e}")

                 # Close context and browser
                 context.close()
                 browser.close()

                 # Playwright saves the video on context close, rename if needed
                 if video_path and context_args.get("record_video_dir"):
                    # Playwright generates a random name, find and rename it
                    try:
                        # Find the most recent mp4 file in the output dir
                        video_files = list(output_dir.glob('*.mp4'))
                        if video_files:
                            generated_video = max(video_files, key=lambda f: f.stat().st_mtime)
                            generated_video.rename(video_path)
                            result["outputs"]["video"] = str(video_path)
                            logger.info(f"Video file renamed to {video_path}")
                        else:
                             logger.warning("Video recording was enabled, but no video file was found.")
                    except Exception as e:
                        logger.error(f"Error renaming video file: {e}")

    except Error as e:
        result["message"] = f"Playwright initialization failed: {e}"
        logger.error(result["message"])
    except Exception as e:
        result["message"] = f"An unexpected error occurred: {e}"
        logger.error(result["message"], exc_info=True)

    logger.info(f"Session recording finished with status: {result['status']}")
    return result


def pwd():
    """Returns the current working directory."""
    return str(Path.cwd())

