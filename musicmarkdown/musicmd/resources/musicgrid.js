var getJSON = function(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      var status = xhr.status;
      if (status === 200) {
        callback(null, xhr.response);
      } else {
        callback(status, xhr.response);
      }
    };
    xhr.send();
};

setInterval(function () {
    getJSON(server_address + '/is_changed/',
        function(err, data) {
          if (err !== null) {
            alert('Something went wrong: ' + err);
          } else {
              if (data.is_changed) {
                location.reload();
              }
          }
        }
        );
    }, 500)