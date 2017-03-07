var filter = document.getElementById("tag-filter");

filter.addEventListener("input", function () {
    var re = new RegExp(filter.value, "i");

    var tags = document.getElementsByClassName("tags")[0].getElementsByClassName("field");

    for (var i = 0; i < tags.length; i++) {
      var label = tags[i].getElementsByTagName("label")[0];
      if (re.test(label.innerHTML)) {
        tags[i].style.display = "block";
      } else {
        tags[i].style.display = "none";
      }
    }
})
