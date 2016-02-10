//used on edit and new menu and restaurant pages to make sure all fields are filled out
function validateForm(formName){
    
    var x = document.getElementById(formName).elements;
    for(var i=0; i<x.length;i++){
	if (x[i].value==null || x[i].value==''){
	    alert('Please fill out all fields');
	    return false;
	    }
    
    
    }}
    
//currently used only on the menu display page to remove empty menu sections
//Removes all empty menu sections to clean up page
//if menu items have somehow been inserted into the database without a 'course' they will not show up
//so be careful if manually editing database
function checkEmpties(){
var x =['appetizers','soupsalad','entrees','drinks','dessert']
c=0
for(var i=0; i<x.length; i++){
   var y = document.getElementById(x[i]).innerHTML;
   if(y.length<65){
       document.getElementById(x[i]).style.display='none';
       c=c+1
       }
    } 
if (c==5){
    document.getElementById('emptyAlert').innerHTML="Menu is currently empty";
    }
}
