import rpy2.robjects.packages as rpackages
from rpy2.robjects.packages import importr
import os
import rpy2.robjects as robjects
from sqlalchemy import create_engine


engine = create_engine('sqlite:///:memory:')

def install_and_load():
    utils = rpackages.importr("utils")
    utils.install_packages("tictoc")
    utils.install_packages("progressr")
    utils.install_packages("wehoop")

    output_path = os.path.expanduser("~/desktop/wnba_web/test/wnbaboxscore.csv")


    r_script = f"""
    library(tictoc)
    library(progressr)
    library(wehoop)

    tic()
    with_progress({{
        wnba_player_box <- load_wnba_player_box()
    }})
    toc()

    write.csv(wnba_player_box, "{output_path}", row.names = FALSE)
    """

    robjects.r(r_script)
