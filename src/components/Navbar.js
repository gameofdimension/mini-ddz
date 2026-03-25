import React from "react";
import { Link, useLocation } from 'react-router-dom';
import logo_white from "../assets/images/logo_white.png";
import GitHubIcon from "@material-ui/icons/GitHub";
import AppBar from "@material-ui/core/AppBar";

function Navbar({subtitleMap}) {
    let location = useLocation();
    console.log(location.pathname, subtitleMap);
    const subtitle = subtitleMap[location.pathname];

    return (
        <AppBar position="fixed" className={"header-bar-wrapper"}>
            <div className={"header-bar"}>
                <Link to="/pve/doudizhu-demo"><img src={logo_white} alt={"Logo"} height="65px" /></Link>
                <div className={"title unselectable"}><div className={"title-text"}>Showdown<span className={"subtitle"}>{subtitle ? '/ ' + subtitle : ''}</span></div></div>
                <div className={"stretch"} />
                <div className={"github-info"} onClick={()=>{window.location.href = 'https://github.com/datamllab/rlcard'}}>
                    <div className={"github-icon"}><GitHubIcon /></div>
                    <div className={"github-text"}>Github</div>
                </div>
            </div>
        </AppBar>
        )

}

export default Navbar;
