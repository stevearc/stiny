angular.module('stiny')

# Navigation bar to switch between pages
.directive('stNavbar', ['CONST', (CONST) ->
  templateUrl: "#{ CONST.URL_PREFIX }/app/navbar.html"
  restrict: 'A'
  replace: true
  controller: 'NavCtrl'
])

.controller('NavCtrl', ['$scope', '$location', 'stAuth', 'CONST',
($scope, $location, stAuth, CONST) ->
  $scope.logout = ->
    stAuth.logout()
])
