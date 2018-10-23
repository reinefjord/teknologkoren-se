function init_widget (widget) {
  var id = widget.id.substring(16);  // Everything after "billetto_widget_"
  console.log(id);
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "https://billetto.se/e/" + id + "/widget_new?theme=white", true );
  xhr.onload = function (e) {
    if ( xhr.readyState == 4 && (xhr.status == 200 || xhr.status == 304) ) {
      widget.innerHTML = xhr.responseText;
    }
  };
  xhr.send(null);
}

function init_widgets () {
  var widgets = document.querySelectorAll('*[id^=billetto_widget_]');
  for (var i = 0; i < widgets.length; i++) {
    init_widget(widgets[i]);
  }
}

init_widgets();
