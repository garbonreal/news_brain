
function gettime(){
    var date = new Date();
    var strDate = date.getHours()+':'+date.getMinutes()+':'+date.getSeconds()+':'+date.getMilliseconds();
    document.getElementById("time").innerHTML = strDate;
}
