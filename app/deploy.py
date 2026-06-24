import zipfile , shutil , tempfile , subprocess
from pathlib import Path
from app.config import settings

class DeployError(ValueError):
    pass


class Deployer:
    def __init__(self , sites_dir : Path, max_uncompressed : int  , max_files: int , clone_timeout : int) -> None:
        self.sites_dir = sites_dir or settings.site_dir
        self.max_uncompressed = max_uncompressed or settings.max_uncompressed
        self.max_files = max_files or settings.max_files
        self.clone_timeout = clone_timeout or settings.clone_timeout
        
    def safe_extract(self , zip_path:str , dest:Path)->None:
        dest.mkdir(parents=True , exist_ok=True)
        dest_resolved = dest.resolve()
        
        with zipfile.ZipFile(zip_path) as z:
            infos = z.infolist()
            
            if len(infos) > self.max_files:
                raise DeployError("archive contains too many files")
            
            total = 0
            for info in infos:
                target = (dest/info.filename).resolve()
                if not str(target).startswith(str(dest_resolved)):
                    raise DeployError("unauthorized path")

                total += info.file_size
                if total > self.max_uncompressed:
                    raise DeployError("uncompressed archive too large")

            z.extractall(dest)
            
    
    def find_web_root(self,  extracted : Path)->Path:
        if(extracted/"index.html").exists():
            return extracted
        
        subdirs = [p for p in extracted.iterdir() if p.is_dir()]
        
        if len(subdirs) == 1 and (subdirs[0]/"index.html").exists():
            return subdirs[0]
        
        for p in extracted.rglob("index.html"):
            return p.parent
        
        if (extracted/"package.json").exists():
            raise DeployError(
                "no index.html found; this looks like source code."
                "Run `npm run build` and upload the output folder(dist/ or build/)"
            )
        
        
        raise DeployError("no index.html found in upload")
    
    
    def fetch_github(self , repo_url:str)->Path:
        if not repo_url.startswith("https://github.com/"):
           raise DeployError("invalid github url")
       
        tmp = Path(tempfile.mkdtemp())
       
        try:
            subprocess.run(
               ["git" , "clone" , "--depth" , "1" , repo_url , str(tmp)],
               check=True,
               timeout= self.clone_timeout
           )
            shutil.rmtree(tmp/".git" , ignore_errors=True)
            return tmp 
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmp, ignore_errors=True)
            raise DeployError("git clone time out")
        except subprocess.CalledProcessError:
            shutil.rmtree(tmp , ignore_errors=True)
            raise DeployError("git clone failed (private url)")
            

    def place(self , web_root : Path , subdomain :str)-> Path:
        target = self.sites_dir / subdomain
        if target.exists():
            raise DeployError("subdomain already exists")
        target.parent.mkdir(parents=True , exist_ok=True)
        shutil.move(str(web_root) , str(target))
        return target