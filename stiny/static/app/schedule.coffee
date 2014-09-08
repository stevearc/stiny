angular.module('stiny')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/schedule', {
    controller: 'ScheduleCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/schedule.html"
    resolve:
      permReq: ['$http', ($http) ->
        return $http.get('/api/home/perm_schedule')
      ]
  })
])

.controller('ScheduleCtrl', ['$scope', '$http', '$filter', 'stToast', 'permReq',
($scope, $http, $filter, stToast, permReq) ->
  $scope.schedulePerms = permReq.data.perms
  $scope.perms = {
    unlock: true
  }

  today = new Date()
  $scope.formatDate = (timestamp) ->
    date = new Date(timestamp)
    if date.getYear() == today.getYear()
      format = 'MMM d HH:MM'
    else
      format = 'MMM d, yyyy HH:MM'
    return $filter('date')(date, format)

  $scope.remove = (index) ->
    perm = $scope.schedulePerms[index]
    data =
      email: perm.email
      start: Math.floor(perm.start / 1000)
    $http.post("/api/home/perm_schedule_del", data).success((data, status, headers, config) ->
      $scope.schedulePerms.splice(index, 1)
    ).error((data, status, headers, config) ->
      stToast.toast("Could not delete")
    )


  $scope.schedule = ->
    if not $scope.email?.length > 0
      stToast.toast("Email required")
      return
    perms = (k for k, v of $scope.perms when v)
    if perms.length == 0
      stToast.toast("Grant at least one permission")
      return
    if $scope.end < $scope.start
      stToast.toast("Permissions can't end before they start")
      return

    $scope.scheduling = true
    data = {
      email: $scope.email
      perms: perms
      start: Math.floor($scope.start.getTime() / 1000)
      end: Math.floor($scope.end.getTime() / 1000)
    }
    $http.post("/api/home/perm_schedule", data).success((data, status, headers, config) ->
      $scope.scheduling = false
      $scope.schedulePerms.push(data.perm)
      $scope.email = ''
    ).error((data, status, headers, config) ->
      $scope.scheduling = false
      stToast.toast("Error saving schedule")
    )
])

.directive('stRangePicker', ['CONST', (CONST) ->
  templateUrl: "#{ CONST.URL_PREFIX }/app/range.html"
  restrict: 'A'
  replace: true
  controller: 'RangePickerCtrl'
  scope:
    start: '='
    end: '='
])

.controller('RangePickerCtrl', ['$scope', ($scope) ->
  isoDate = new Date().toISOString()
  $scope.today = isoDate.slice(0, isoDate.indexOf('T'))
  $scope.foo = 'fuck'
  $scope.startDate = new Date()
  $scope.endDate = new Date()
  $scope.startTime = new Date()
  $scope.startTime.setHours(0)
  $scope.startTime.setMinutes(0)
  $scope.startTime.setSeconds(0)
  $scope.endTime = new Date()
  $scope.endTime.setHours(23)
  $scope.endTime.setMinutes(0)
  $scope.endTime.setSeconds(0)
  $scope.open = {}

  updateResults = ->
    $scope.start = new Date($scope.startDate)
    $scope.start.setHours($scope.startTime.getHours())
    $scope.start.setMinutes($scope.startTime.getMinutes())
    $scope.start.setSeconds($scope.startTime.getSeconds())
    $scope.end = new Date($scope.endDate)
    $scope.end.setHours($scope.endTime.getHours())
    $scope.end.setMinutes($scope.endTime.getMinutes())
    $scope.end.setSeconds($scope.endTime.getSeconds())

  $scope.$watch('startDate', updateResults)
  $scope.$watch('startTime', updateResults)
  $scope.$watch('endDate', updateResults)
  $scope.$watch('endTime', updateResults)

  $scope.open = ($event, name) ->
    $event.preventDefault()
    $event.stopPropagation()
    $scope.open[name] = true
])
