jQuery(document).ready(function() { 

$(".clickable-row").click(function() { 
    window.location = $(this).data("url"); 
}); 

$('#sumTable').DataTable();
$('.dataTables_length').addClass('bs-select');

$("button#filterSuc").click(function(event){
    event.preventDefault();

    if ($("div>.card.success").hasClass("isHidden")){
        $("div>.card.success").show();
        $("div>.card.success").removeClass("isHidden");
        $(this).removeClass("active");
    }else{
    $("div>.card.success").hide();
    $("div>.card.success").addClass("isHidden");
    $(this).addClass("active");
    };
});

$("button#filterFail").click(function(event){
    event.preventDefault();

    if ($("div>.card.bg-danger").hasClass("isHidden")){
        $("div>.card.bg-danger").show();
        $("div>.card.bg-danger").removeClass("isHidden");
        $(this).removeClass("active");
    }else{
    $("div>.card.bg-danger").hide();
    $("div>.card.bg-danger").addClass("isHidden");
    $(this).addClass("active");
    };
});
});



