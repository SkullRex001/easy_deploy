import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI , UploadFile , HTTPException
from pydantic import BaseModel

from app.config import settings
from app.deploy import Deployer , DeployError
from app.subdomain import SubdomainGenerator , SubdomainError


app = FastAPI()

deployer = Deployer(
    sites_dir=settings.site_dir,
    max_uncompressed=settings.max_uncompressed,
    max_files=settings.max_files,
    clone_timeout=settings.clone_timeout
)

subdomain_gen = SubdomainGenerator(sites_dir=settings.site_dir)

class GithubRequest(BaseModel):
    repo_url:str
    
def _make_url(subdomain:str)-> str:
    return f"http://{subdomain}.{settings.base_domain}"

@app.post("/deploy/upload")
async def deploy_upload(file: UploadFile):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400 , "must be a .zip file")
    
    tmp = Path(tempfile.mkdtemp())
    try:
        zip_path = tmp/"upload.zip"
        with open(zip_path , "wb") as f:
            shutil.copyfileobj(file.file , f)
            
        extracted = tmp/"extracted"
        deployer.safe_extract(str(zip_path) , extracted)
        
        web_root = deployer.find_web_root(extracted)
        subdomain = subdomain_gen.generate()
        deployer.place(web_root , subdomain)
        
        return {"subdomain" : subdomain , "url" : _make_url(subdomain)}
    
    except (DeployError , SubdomainError) as e:
        raise HTTPException(400 , str(e))
    finally:
        shutil.rmtree(tmp , ignore_errors=True)
    
    

@app.post("/deploy/github")
async def deploy_github(req: GithubRequest):
    cloned = None
    
    try:
        cloned = deployer.fetch_github(req.repo_url)
           
        web_root = deployer.find_web_root(cloned)
        subdomain = subdomain_gen.generate()
        deployer.place(web_root , subdomain)
        
        return {"subdomin" : subdomain , "url" : _make_url(subdomain)}
    
    except(DeployError , SubdomainError) as e:
        raise HTTPException(400 , str(e))
    finally:
        if cloned and cloned.exists():
            shutil.rmtree(cloned , ignore_errors=True)
            

@app.get("/health")
async def health():
    return {"status" : "ok"}