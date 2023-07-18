<!-- 解决CSRF-->
$(function () {
    $.ajaxSetup({
        headers: {"X-CSRFToken": getCookie("csrftoken")}
    });
    //Initialize Select2 Elements
    $('.select2bs4').select2({
        theme: 'bootstrap4',
        placeholder: "请选择",
        //allowClear: true,
    });
    //Bootstrap Duallistbox
    $('.duallistbox').bootstrapDualListbox({
        nonSelectedListLabel: '未选择',
        selectedListLabel: '已选择',
        preserveSelectionOnMove: 'moved',
        moveOnSelect: false,           // 出现一个剪头，表示可以一次选择一个
        filterTextClear: '展示所有',
        moveSelectedLabel: "添加",
        moveAllLabel: '添加所有',
        removeSelectedLabel: "移除",
        removeAllLabel: '移除所有',
        infoText: '共{0}个',
        showFilterInputs: true,       // 是否带搜索
        selectorMinimalHeight: 160
    })
});
Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000
});
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 解决下拉筛选项被表格遮挡
// https://github.com/twbs/bootstrap/issues/11037#issuecomment-274870381
$('.table-responsive').on('shown.bs.dropdown', function (e) {
    var t = $(this),
        m = $(e.target).find('.dropdown-menu'),
        tb = t.offset().top + t.height(),
        mb = m.offset().top + m.outerHeight(true),
        d = 20; // Space for shadow + scrollbar.
    if (t[0].scrollWidth > t.innerWidth()) {
        if (mb + d > tb) {
            t.css('padding-bottom', ((mb + d) - tb));
        }
    } else {
        t.css('overflow', 'visible');
    }
}).on('hidden.bs.dropdown', function () {
    $(this).css({'padding-bottom': '', 'overflow': ''});
}).on('page-change.bs.table', function () {
    $(this).css({'padding-bottom': '', 'overflow': ''});
});

$(function() {
    var url = window.location;
    // var element = $('ul.nav a').filter(function() {
    //     return this.href == url;
    // }).addClass('active').parent().parent().addClass('in').parent();
    var element = $('ul.nav a').filter(function() {
        return this.href == url;
    }).addClass('active').parent().parent();

    while (true) {
        console.log(element);
        if (element.is('ul') & element.parent().is('li')){
            element = element.parent().addClass('menu-open');
        } else {
            break;
        }
    }
});
var onLoadErrorCallback = function (status, jqXHR) {
    if (status === 403) {
        Toast.fire({
            icon: 'error',
            text: "权限错误，您没有权限查看该数据！",
            title: "操作失败"
        });
    } else {
        Toast.fire({
            icon: 'error',
            text: "未知错误，请联系管理员处理！",
            title: "操作失败"
        });
    }
};

function assets_type_display(value) {
    if (value === "server") {
        return "<span class=\"btn btn-info btn-sm\">物理机</span>"
    }
    else if (value === "vmser") {
        return "<span class=\"btn btn-default btn-sm\">虚拟机</span>"
    }
    else if (value === "switch") {
        return "<span class=\"btn btn-info btn-sm\">交换机</span>"
    }
    else if (value === "route") {
        return "<span class=\"label label-warning\">路由器</span>"
    }
    else if (value === "printer") {
        return "<span class=\"label label-warning\">打印机</span>"
    }
    else if (value === "firewall") {
        return "<span class=\"label label-info \">防火墙</span>"
    }
    else if (value === "storage") {
        return "<span class=\"label label-primary\">存储设备</span>"
    }
    else if (value === "wifi") {
        return "<span class=\"label label-danger\">无线设备</span>"
    }
    else  {
        return "<span class=\"label label-danger\">其它设备</span>"
    }
}

function sqlworkflowStatus_formatter(value){
    if(value==="finish"){
        return "<span class=\"badge badge-success\">正常结束</span>"
    }else if(value==="abort"){
        return "<span class=\"badge badge-default\">终止流程</span>"}
    else if(value==="manreviewing"){return "<span class=\"badge badge-info\">等待审核</span>"}
    else if(value==="review_pass"){return "<span class=\"badge badge-warning\">审核通过</span>"}
    else if(value==="timingtask"){return "<span class=\"badge badge-warning\">定时执行</span>"}
    else if(value==="queuing"){return "<span class=\"badge badge-info \">排队中</span>"}
    else if(value==="executing"){return "<span class=\"badge badge-primary\">执行中</span>"}
    else if(value==="autoreviewwrong"){return "<span class=\"badge badge-danger\">自动审核不通过</span>"}
    else if(value==="exception"){return "<span class=\"badge badge-danger\">执行异常</span>"}
    else{
        return "<span class=\"badge badge-danger\">"+"未知状态"+"</span>"
    }
}